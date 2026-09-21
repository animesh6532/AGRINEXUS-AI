"""
Singleton Model Registry for AgriNexus AI backend.
Loads all 7 frozen ML artifacts once during startup, validates contracts, runs smoke tests,
and exposes unified, read-only inference services.
"""

import os
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torchvision import models

from ..core.config import settings, PROJECT_ROOT
from ..core.logging import logger
from .cv_service import CVService
from .gradcam import GradCAM


def _to_python_type(val: Any) -> Any:
    """Helper function to convert NumPy / PyTorch types into native JSON-serializable Python types."""
    if isinstance(val, (np.integer, int)):
        return int(val)
    elif isinstance(val, (np.floating, float)):
        return float(val)
    elif isinstance(val, np.ndarray):
        return val.tolist()
    elif isinstance(val, torch.Tensor):
        return val.detach().cpu().numpy().tolist()
    return val


class ModelStatusInfo:
    def __init__(self, key: str, task: str, artifact_name: str, framework: str):
        self.key = key
        self.task = task
        self.artifact_name = artifact_name
        self.framework = framework
        self.status = "UNAVAILABLE"
        self.artifact_path = ""
        self.last_error: Optional[str] = None


class ModelRegistry:
    """Singleton Registry managing frozen ML models."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.models_meta: Dict[str, ModelStatusInfo] = {
            "crop": ModelStatusInfo("crop", "crop_recommendation", "crop_recommendation.pkl", "scikit-learn"),
            "disease": ModelStatusInfo("disease", "plant_disease_detection", "disease_detection.pt", "PyTorch"),
            "fertilizer": ModelStatusInfo("fertilizer", "fertilizer_recommendation", "fertilizer_recommendation.pkl", "scikit-learn"),
            "irrigation": ModelStatusInfo("irrigation", "irrigation_prediction", "irrigation_prediction.pkl", "scikit-learn"),
            "pest_visual": ModelStatusInfo("pest_visual", "visual_pest_classification", "pest_prediction.pkl", "PyTorch"),
            "pest_env": ModelStatusInfo("pest_env", "environmental_pest_risk", "pest_prediction.pkl", "scikit-learn"),
            "soil": ModelStatusInfo("soil", "soil_organic_carbon_analysis", "soil_analysis.pkl", "scikit-learn"),
            "yield": ModelStatusInfo("yield", "crop_yield_prediction", "yield_prediction.pkl", "XGBoost")
        }

        # Loaded model artifact storage
        self.crop_artifact: Optional[Dict[str, Any]] = None
        self.disease_artifact: Optional[Dict[str, Any]] = None
        self.disease_model: Optional[torch.nn.Module] = None
        self.disease_gradcam: Optional[GradCAM] = None

        self.fertilizer_artifact: Optional[Dict[str, Any]] = None
        self.irrigation_artifact: Optional[Dict[str, Any]] = None

        self.pest_artifact: Optional[Dict[str, Any]] = None
        self.pest_visual_model: Optional[torch.nn.Module] = None

        self.soil_artifact: Optional[Dict[str, Any]] = None
        self.yield_artifact: Optional[Dict[str, Any]] = None

    def _locate_artifact(self, filename: str) -> Optional[Path]:
        """Locate model artifact file across standard candidate directories."""
        candidate_dirs = []

        if settings.MODEL_DIR:
            candidate_dirs.append(Path(settings.MODEL_DIR))

        # Check root models/ first, then Notebook/models/
        candidate_dirs.append(PROJECT_ROOT / "models")
        candidate_dirs.append(PROJECT_ROOT / "Notebook" / "models")
        candidate_dirs.append(PROJECT_ROOT / "backend" / "models")

        for d in candidate_dirs:
            p = d / filename
            if p.exists():
                return p
        return None

    def load_all_models(self):
        """Load and validate all 7 frozen ML model artifacts during application startup."""
        logger.info("Initializing Model Registry — loading frozen model artifacts...")

        self._load_crop_model()
        self._load_disease_model()
        self._load_fertilizer_model()
        self._load_irrigation_model()
        self._load_pest_models()
        self._load_soil_model()
        self._load_yield_model()

        ready_count = sum(1 for m in self.models_meta.values() if m.status == "READY")
        logger.info(f"Model Registry initialization complete. {ready_count}/{len(self.models_meta)} services READY.")

    # ------------------------------------------------------------------
    # 1. CROP RECOMMENDATION
    # ------------------------------------------------------------------
    def _load_crop_model(self):
        meta = self.models_meta["crop"]
        path = self._locate_artifact(meta.artifact_name)
        if not path:
            meta.last_error = f"Artifact file {meta.artifact_name} not found."
            logger.error(meta.last_error)
            return

        meta.artifact_path = str(path)
        try:
            with open(path, "rb") as f:
                self.crop_artifact = pickle.load(f)

            # Smoke Test (ExtraTrees champion model was trained on RAW feature values)
            feats = self.crop_artifact["feature_cols"]
            sample_df = pd.DataFrame([[90.0, 42.0, 43.0, 20.87, 82.0, 6.5, 202.9]], columns=feats)
            pred = self.crop_artifact["model"].predict(sample_df)

            meta.status = "READY"
            logger.info("Loaded crop_recommendation model successfully.")
        except Exception as e:
            meta.status = "UNAVAILABLE"
            meta.last_error = str(e)
            logger.error(f"Failed loading crop model: {e}")

    def predict_crop(self, features_dict: Dict[str, float]) -> Dict[str, Any]:
        if self.models_meta["crop"].status != "READY":
            raise RuntimeError("Crop Recommendation model is UNAVAILABLE.")

        feats = self.crop_artifact["feature_cols"]
        row = [features_dict[k] for k in feats]
        df = pd.DataFrame([row], columns=feats)

        # 1. Model prediction on raw features (ExtraTrees model trained on unscaled features)
        probs = self.crop_artifact["model"].predict_proba(df)[0]
        class_names = self.crop_artifact["class_names"]

        top_idx = np.argmax(probs)
        pred_label = str(class_names[top_idx])
        top_conf = float(probs[top_idx])

        # Top K probabilities
        top_k_indices = np.argsort(probs)[::-1][:3]
        top_k = [
            {"crop": str(class_names[i]), "probability": round(float(probs[i]), 4)}
            for i in top_k_indices
        ]

        # 2. Isolation Forest Anomaly Detection
        iso_pred = self.crop_artifact["isolation_forest"].predict(df)[0]
        is_plausible = bool(iso_pred == 1)
        anomaly_msg = "Plausible agronomic input" if is_plausible else "Out-of-distribution input profile detected by IsolationForest"

        return {
            "prediction": pred_label,
            "confidence": round(top_conf, 4),
            "top_k_predictions": top_k,
            "is_plausible": is_plausible,
            "anomaly_status": anomaly_msg
        }

    # ------------------------------------------------------------------
    # 2. PLANT DISEASE DETECTION
    # ------------------------------------------------------------------
    def _load_disease_model(self):
        meta = self.models_meta["disease"]
        path = self._locate_artifact(meta.artifact_name)
        if not path:
            meta.last_error = f"Artifact file {meta.artifact_name} not found."
            logger.error(meta.last_error)
            return

        meta.artifact_path = str(path)
        try:
            self.disease_artifact = torch.load(path, map_location="cpu")
            num_classes = self.disease_artifact["num_classes"]

            # Reconstruct ResNet18 model
            model = models.resnet18(weights=None)
            model.fc = nn.Linear(model.fc.in_features, num_classes)
            model.load_state_dict(self.disease_artifact["model_state_dict"])
            model.eval()

            self.disease_model = model

            # Attach Grad-CAM generator to layer4[-1]
            try:
                self.disease_gradcam = GradCAM(self.disease_model, self.disease_model.layer4[-1])
            except Exception as cam_err:
                logger.warning(f"GradCAM initialization warning: {cam_err}")
                self.disease_gradcam = None

            # Smoke Test on dummy tensor
            dummy_tensor = torch.zeros(1, 3, 224, 224)
            with torch.no_grad():
                _ = self.disease_model(dummy_tensor)

            meta.status = "READY"
            logger.info("Loaded disease_detection model successfully.")
        except Exception as e:
            meta.status = "UNAVAILABLE"
            meta.last_error = str(e)
            logger.error(f"Failed loading disease model: {e}")

    def predict_disease(self, image_bytes: bytes, include_gradcam: bool = False) -> Dict[str, Any]:
        if self.models_meta["disease"].status != "READY":
            raise RuntimeError("Disease Detection model is UNAVAILABLE.")

        # 1. OpenCV Quality Report
        quality_report = CVService.inspect_image_bytes(image_bytes)

        # 2. PyTorch Preprocessing
        tensor, pil_img = CVService.preprocess_for_pytorch(image_bytes)

        # 3. Model Inference
        with torch.no_grad():
            logits = self.disease_model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze().numpy()

        class_names = self.disease_artifact["class_names"]
        top_idx = int(np.argmax(probs))
        pred_label = str(class_names[top_idx])
        top_conf = float(probs[top_idx])

        # Top 3 predictions
        top_k_indices = np.argsort(probs)[::-1][:3]
        top_k = [
            {"disease": str(class_names[i]), "probability": round(float(probs[i]), 4)}
            for i in top_k_indices
        ]

        # 4. Optional Grad-CAM Heatmap (Only generated when explicitly requested; failures cleanly log warning)
        gradcam_b64 = None
        gradcam_avail = False
        if include_gradcam and self.disease_gradcam is not None:
            try:
                gradcam_b64 = self.disease_gradcam.generate_heatmap_base64(
                    input_tensor=tensor,
                    pil_image=pil_img,
                    target_class_idx=top_idx
                )
                gradcam_avail = (gradcam_b64 is not None)
            except Exception as cam_err:
                logger.warning(f"GradCAM generation error: {cam_err}")
                gradcam_b64 = None
                gradcam_avail = False

        return {
            "predicted_disease": pred_label,
            "confidence": round(top_conf, 4),
            "top_k_predictions": top_k,
            "image_quality": quality_report,
            "gradcam_available": gradcam_avail,
            "gradcam_heatmap": gradcam_b64
        }


    # ------------------------------------------------------------------
    # 3. FERTILIZER RECOMMENDATION
    # ------------------------------------------------------------------
    def _load_fertilizer_model(self):
        meta = self.models_meta["fertilizer"]
        path = self._locate_artifact(meta.artifact_name)
        if not path:
            meta.last_error = f"Artifact file {meta.artifact_name} not found."
            logger.error(meta.last_error)
            return

        meta.artifact_path = str(path)
        try:
            with open(path, "rb") as f:
                self.fertilizer_artifact = pickle.load(f)

            pipe = self.fertilizer_artifact["model_pipeline"]
            feats = self.fertilizer_artifact["feature_cols"]

            sample_df = pd.DataFrame([{
                "Nitrogen": 20.0, "Phosphorus": 20.0, "Potassium": 20.0,
                "pH": 6.5, "Rainfall": 800.0, "Temperature": 26.0,
                "District_Name": "Pune", "Soil_color": "Black", "Crop": "Sugarcane",
                "Link": "https://example.com"
            }])[feats]

            _ = pipe.predict(sample_df)

            meta.status = "READY"
            logger.info("Loaded fertilizer_recommendation model successfully.")
        except Exception as e:
            meta.status = "UNAVAILABLE"
            meta.last_error = str(e)
            logger.error(f"Failed loading fertilizer model: {e}")

    def predict_fertilizer(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        if self.models_meta["fertilizer"].status != "READY":
            raise RuntimeError("Fertilizer Recommendation model is UNAVAILABLE.")

        pipe = self.fertilizer_artifact["model_pipeline"]
        feats = self.fertilizer_artifact["feature_cols"]
        classes = self.fertilizer_artifact["classes"]

        df = pd.DataFrame([input_dict])[feats]
        pred_val = pipe.predict(df)[0]
        pred_label = str(pred_val)

        probs_list = []
        top_conf = None
        if hasattr(pipe, "predict_proba"):
            try:
                probs = pipe.predict_proba(df)[0]
                top_idx = np.argmax(probs)
                top_conf = float(probs[top_idx])

                top_k_idx = np.argsort(probs)[::-1][:3]
                probs_list = [
                    {"formulation": str(classes[i]), "probability": round(float(probs[i]), 4)}
                    for i in top_k_idx if i < len(classes)
                ]
            except Exception:
                pass

        return {
            "predicted_formulation": pred_label,
            "confidence": round(top_conf, 4) if top_conf is not None else None,
            "top_k_predictions": probs_list
        }

    # ------------------------------------------------------------------
    # 4. IRRIGATION PREDICTION
    # ------------------------------------------------------------------
    def _load_irrigation_model(self):
        meta = self.models_meta["irrigation"]
        path = self._locate_artifact(meta.artifact_name)
        if not path:
            meta.last_error = f"Artifact file {meta.artifact_name} not found."
            logger.error(meta.last_error)
            return

        meta.artifact_path = str(path)
        try:
            with open(path, "rb") as f:
                self.irrigation_artifact = pickle.load(f)

            scaler = self.irrigation_artifact["scaler"]
            model = self.irrigation_artifact["model"]
            feats = self.irrigation_artifact["feature_cols"]

            sample_df = pd.DataFrame([[0.22, 0.225, 0.23, 0.235, 0.23, 0.0, 0.0]], columns=feats)
            scaled = scaler.transform(sample_df)
            _ = model.predict(scaled)

            meta.status = "READY"
            logger.info("Loaded irrigation_prediction model successfully.")
        except Exception as e:
            meta.status = "UNAVAILABLE"
            meta.last_error = str(e)
            logger.error(f"Failed loading irrigation model: {e}")

    def predict_irrigation(self, input_dict: Dict[str, float]) -> Dict[str, Any]:
        if self.models_meta["irrigation"].status != "READY":
            raise RuntimeError("Irrigation Prediction model is UNAVAILABLE.")

        scaler = self.irrigation_artifact["scaler"]
        model = self.irrigation_artifact["model"]
        feats = self.irrigation_artifact["feature_cols"]

        row = [input_dict[k] for k in feats]
        df = pd.DataFrame([row], columns=feats)
        scaled = scaler.transform(df)

        ml_pred_swc = float(model.predict(scaled)[0])

        # Persistence Baseline: SWC_{t+3h} = SWC_t
        curr_swc = float(input_dict["SWC"])

        thresholds = self.irrigation_artifact.get("agronomic_thresholds", {
            "field_capacity": 0.32,
            "wilting_point": 0.14,
            "critical_threshold": 0.23
        })
        crit_thresh = thresholds["critical_threshold"]

        need_irrigation = ml_pred_swc < crit_thresh
        msg = "Soil water content below critical threshold. Irrigation recommended." if need_irrigation else "Soil water content adequate."

        agronomic_status = {
            "field_capacity": thresholds["field_capacity"],
            "wilting_point": thresholds["wilting_point"],
            "critical_threshold": crit_thresh,
            "irrigation_needed": need_irrigation,
            "status_message": msg,
            "decision_note": "Threshold status evaluates ML predicted 3-hour SWC against critical threshold. Note that Persistence Baseline (SWC_t+3h = SWC_t) is the primary benchmark reference."
        }

        return {
            "ml_predicted_swc_3h": round(ml_pred_swc, 4),
            "persistence_swc_3h": round(curr_swc, 4),
            "agronomic_status": agronomic_status
        }


    # ------------------------------------------------------------------
    # 5. PEST PREDICTION (Visual + Environmental)
    # ------------------------------------------------------------------
    def _load_pest_models(self):
        meta_v = self.models_meta["pest_visual"]
        meta_e = self.models_meta["pest_env"]
        path = self._locate_artifact(meta_v.artifact_name)

        if not path:
            err = f"Artifact file {meta_v.artifact_name} not found."
            meta_v.last_error = err
            meta_e.last_error = err
            logger.error(err)
            return

        meta_v.artifact_path = str(path)
        meta_e.artifact_path = str(path)

        try:
            with open(path, "rb") as f:
                self.pest_artifact = pickle.load(f)

            # 1. Visual Model (MobileNetV3 Small)
            num_classes = self.pest_artifact["num_classes"]
            mobilenet = models.mobilenet_v3_small(weights=None)
            # Reconstruct classifier head matching notebook architecture
            in_features = mobilenet.classifier[3].in_features
            mobilenet.classifier[3] = nn.Linear(in_features, num_classes)
            mobilenet.load_state_dict(self.pest_artifact["visual_model_state"])
            mobilenet.eval()
            self.pest_visual_model = mobilenet

            # Visual smoke test
            dummy_tensor = torch.zeros(1, 3, 224, 224)
            with torch.no_grad():
                _ = self.pest_visual_model(dummy_tensor)

            meta_v.status = "READY"
            logger.info("Loaded visual pest_prediction model successfully.")
        except Exception as e:
            meta_v.status = "UNAVAILABLE"
            meta_v.last_error = str(e)
            logger.error(f"Failed loading visual pest model: {e}")

        try:
            # 2. Environmental Pest Risk Model Pipeline
            env_pipe = self.pest_artifact["env_model_pipeline"]
            sample_df = pd.DataFrame([{
                "Temperature": 28.5, "Humidity": 75.0, "Rainfall": 120.0,
                "Crop_Type": "Rice", "Soil_Type": "Clay", "Region": "South"
            }])
            _ = env_pipe.predict(sample_df)

            meta_e.status = "READY"
            logger.info("Loaded environmental pest_risk model successfully.")
        except Exception as e:
            meta_e.status = "UNAVAILABLE"
            meta_e.last_error = str(e)
            logger.error(f"Failed loading environmental pest model: {e}")

    def predict_pest_visual(self, image_bytes: bytes) -> Dict[str, Any]:
        if self.models_meta["pest_visual"].status != "READY":
            raise RuntimeError("Visual Pest Classification model is UNAVAILABLE.")

        quality_report = CVService.inspect_image_bytes(image_bytes)
        tensor, _ = CVService.preprocess_for_pytorch(image_bytes)

        with torch.no_grad():
            logits = self.pest_visual_model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze().numpy()

        class_names = self.pest_artifact["class_names"]
        top_idx = int(np.argmax(probs))
        pred_label = str(class_names[top_idx])
        top_conf = float(probs[top_idx])

        top_k_indices = np.argsort(probs)[::-1][:3]
        top_k = [
            {"pest_class": str(class_names[i]), "probability": round(float(probs[i]), 4)}
            for i in top_k_indices
        ]

        return {
            "predicted_pest": pred_label,
            "confidence": round(top_conf, 4),
            "top_k_predictions": top_k,
            "image_quality": quality_report
        }

    def predict_pest_risk(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        if self.models_meta["pest_env"].status != "READY":
            raise RuntimeError("Environmental Pest Risk model is UNAVAILABLE.")

        env_pipe = self.pest_artifact["env_model_pipeline"]
        df = pd.DataFrame([input_dict])

        pred_val = env_pipe.predict(df)[0]
        pred_label = str(pred_val)

        top_conf = None
        top_k = []
        if hasattr(env_pipe, "predict_proba"):
            try:
                probs = env_pipe.predict_proba(df)[0]
                classes = env_pipe.classes_
                top_idx = np.argmax(probs)
                top_conf = float(probs[top_idx])

                top_k = [
                    {"risk_level": str(classes[i]), "probability": round(float(probs[i]), 4)}
                    for i in np.argsort(probs)[::-1]
                ]
            except Exception:
                pass

        return {
            "pest_severity_risk": pred_label,
            "confidence": round(top_conf, 4) if top_conf is not None else None,
            "top_k_predictions": top_k
        }

    # ------------------------------------------------------------------
    # 6. SOIL ANALYSIS (SOIL ORGANIC CARBON)
    # ------------------------------------------------------------------
    def _load_soil_model(self):
        meta = self.models_meta["soil"]
        path = self._locate_artifact(meta.artifact_name)
        if not path:
            meta.last_error = f"Artifact file {meta.artifact_name} not found."
            logger.error(meta.last_error)
            return

        meta.artifact_path = str(path)
        try:
            with open(path, "rb") as f:
                self.soil_artifact = pickle.load(f)

            preprocessor = self.soil_artifact["preprocessor"]
            model = self.soil_artifact["model"]
            feats = self.soil_artifact["feature_cols"]

            sample_df = pd.DataFrame([{
                "pH(CaCl2)": 6.2, "pH(H2O)": 6.8, "Clay": 25.0, "Silt": 40.0, "Sand": 35.0,
                "CaCO3": 12.0, "P": 18.5, "N": 2.1, "K": 180.0, "EC": 15.0,
                "NUTS_0": "DE", "LC1": "B11"
            }])[feats]

            proc = preprocessor.transform(sample_df)
            _ = model.predict(proc)

            meta.status = "READY"
            logger.info("Loaded soil_analysis model successfully.")
        except Exception as e:
            meta.status = "UNAVAILABLE"
            meta.last_error = str(e)
            logger.error(f"Failed loading soil model: {e}")

    def predict_soil(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        if self.models_meta["soil"].status != "READY":
            raise RuntimeError("Soil Organic Carbon model is UNAVAILABLE.")

        preprocessor = self.soil_artifact["preprocessor"]
        model = self.soil_artifact["model"]
        feats = self.soil_artifact["feature_cols"]
        margin = float(self.soil_artifact.get("q95_residual_margin", 38.71889))

        df = pd.DataFrame([input_dict])[feats]
        proc = preprocessor.transform(df)

        pred_soc = float(model.predict(proc)[0])
        lower_bound = max(0.0, pred_soc - margin)
        upper_bound = pred_soc + margin

        return {
            "predicted_soc": round(pred_soc, 4),
            "prediction_interval": {
                "lower": round(lower_bound, 4),
                "upper": round(upper_bound, 4),
                "margin": round(margin, 4)
            }
        }

    # ------------------------------------------------------------------
    # 7. YIELD PREDICTION
    # ------------------------------------------------------------------
    def _load_yield_model(self):
        meta = self.models_meta["yield"]
        path = self._locate_artifact(meta.artifact_name)
        if not path:
            meta.last_error = f"Artifact file {meta.artifact_name} not found."
            logger.error(meta.last_error)
            return

        meta.artifact_path = str(path)
        try:
            with open(path, "rb") as f:
                self.yield_artifact = pickle.load(f)

            preprocessor = self.yield_artifact["preprocessor"]
            model = self.yield_artifact["model"]
            feats = self.yield_artifact["feature_cols"]

            sample_df = pd.DataFrame([{
                "Crop": "Rice", "Season": "Kharif", "State": "Punjab",
                "Area": 100.0, "Annual_Rainfall": 1200.0, "Fertilizer": 15000.0,
                "Pesticide": 500.0, "Fertilizer_Per_Area": 150.0, "Pesticide_Per_Area": 5.0
            }])[feats]

            proc = preprocessor.transform(sample_df)
            _ = model.predict(proc)

            meta.status = "READY"
            logger.info("Loaded yield_prediction model successfully.")
        except Exception as e:
            meta.status = "UNAVAILABLE"
            meta.last_error = str(e)
            logger.error(f"Failed loading yield model: {e}")

    def predict_yield(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        if self.models_meta["yield"].status != "READY":
            raise RuntimeError("Yield Prediction model is UNAVAILABLE.")

        preprocessor = self.yield_artifact["preprocessor"]
        model = self.yield_artifact["model"]
        feats = self.yield_artifact["feature_cols"]
        margin = float(self.yield_artifact.get("q95_residual_margin", 7.97502))

        df = pd.DataFrame([input_dict])[feats]
        proc = preprocessor.transform(df)

        pred_yield = float(model.predict(proc)[0])
        lower_bound = max(0.0, pred_yield - margin)
        upper_bound = pred_yield + margin

        return {
            "predicted_yield": round(pred_yield, 4),
            "prediction_interval": {
                "lower": round(lower_bound, 4),
                "upper": round(upper_bound, 4),
                "margin": round(margin, 4)
            }
        }

    # ------------------------------------------------------------------
    # HEALTH REPORTING
    # ------------------------------------------------------------------
    def get_health_status(self) -> Dict[str, Any]:
        """Generate comprehensive model health dictionary for GET /api/v1/models/health."""
        models_summary = {k: m.status for k, m in self.models_meta.items()}
        all_ready = all(status == "READY" for status in models_summary.values())
        overall_status = "healthy" if all_ready else "degraded"

        details = {}
        for k, m in self.models_meta.items():
            details[k] = {
                "status": m.status,
                "task": m.task,
                "artifact_path": m.artifact_path,
                "framework": m.framework,
                "last_error": m.last_error
            }

        return {
            "status": overall_status,
            "models": models_summary,
            "details": details
        }

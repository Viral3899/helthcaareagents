"""
Medical Tools

This module provides medical knowledge, drug information, and clinical decision support tools
for healthcare agents and applications.
"""

from typing import Dict, List, Any, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import logging
import json
import os
from pathlib import Path

class DrugInteractionInput(BaseModel):
    """Input for drug interaction checking"""
    medications: List[str] = Field(description="List of medications to check for interactions")

class MedicalCodeInput(BaseModel):
    """Input for medical code lookup"""
    code: str = Field(description="Medical code to lookup (ICD-10, CPT, etc.)")
    code_type: str = Field(description="Type of medical code (icd10, cpt, etc.)")

class SymptomAnalysisInput(BaseModel):
    """Input for symptom analysis"""
    symptoms: List[str] = Field(description="List of patient symptoms")
    patient_age: Optional[int] = Field(default=None, description="Patient age")
    patient_gender: Optional[str] = Field(default=None, description="Patient gender")

class DrugInteractionTool(BaseTool):
    """Tool for checking drug interactions"""
    name: str = "check_drug_interactions"
    description: str = "Check for potential drug interactions between medications"
    args_schema: type[BaseModel] = DrugInteractionInput
    
    def _run(self, medications: List[str]) -> Dict[str, Any]:
        """Check drug interactions"""
        try:
            # Load drug interaction data
            drug_data = self._load_drug_data()
            
            interactions = []
            contraindications = []
            
            # Check for interactions between all pairs of medications
            for i, med1 in enumerate(medications):
                for j, med2 in enumerate(medications):
                    if i < j:  # Avoid duplicate checks
                        interaction = self._check_medication_pair(med1, med2, drug_data)
                        if interaction:
                            interactions.append(interaction)
            
            # Check individual medication contraindications
            for med in medications:
                contraindication = self._check_contraindications(med, drug_data)
                if contraindication:
                    contraindications.append(contraindication)
            
            return {
                'medications': medications,
                'interactions': interactions,
                'contraindications': contraindications,
                'safe_to_prescribe': len(interactions) == 0 and len(contraindications) == 0,
                'recommendations': self._generate_recommendations(interactions, contraindications)
            }
            
        except Exception as e:
            logging.error(f"Drug interaction check failed: {str(e)}")
            return {
                'error': f"Drug interaction check failed: {str(e)}",
                'medications': medications,
                'interactions': [],
                'contraindications': [],
                'safe_to_prescribe': False
            }
    
    def _load_drug_data(self) -> Dict[str, Any]:
        """Load drug interaction data from JSON file"""
        try:
            data_file = Path(__file__).parent.parent.parent / "data" / "medications.json"
            if data_file.exists():
                with open(data_file, 'r') as f:
                    return json.load(f)
            else:
                # Return basic drug data if file doesn't exist
                return self._get_basic_drug_data()
        except Exception as e:
            logging.error(f"Failed to load drug data: {str(e)}")
            return self._get_basic_drug_data()
    
    def _get_basic_drug_data(self) -> Dict[str, Any]:
        """Get basic drug interaction data"""
        return {
            "interactions": {
                "warfarin": ["aspirin", "ibuprofen", "heparin"],
                "aspirin": ["warfarin", "ibuprofen", "heparin"],
                "ibuprofen": ["warfarin", "aspirin"],
                "heparin": ["warfarin", "aspirin"],
                "metformin": ["insulin", "glipizide"],
                "insulin": ["metformin", "glipizide"],
                "glipizide": ["metformin", "insulin"]
            },
            "contraindications": {
                "warfarin": ["pregnancy", "bleeding_disorders"],
                "aspirin": ["bleeding_disorders", "stomach_ulcers"],
                "ibuprofen": ["kidney_disease", "stomach_ulcers"],
                "metformin": ["kidney_disease", "heart_failure"],
                "insulin": ["hypoglycemia"]
            }
        }
    
    def _check_medication_pair(self, med1: str, med2: str, drug_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check interaction between two medications"""
        interactions = drug_data.get("interactions", {})
        
        med1_lower = med1.lower()
        med2_lower = med2.lower()
        
        # Check if med1 interacts with med2
        if med1_lower in interactions and med2_lower in interactions[med1_lower]:
            return {
                'medication1': med1,
                'medication2': med2,
                'interaction_type': 'drug_drug',
                'severity': 'moderate',
                'description': f"{med1} may interact with {med2}",
                'recommendation': 'Monitor closely and consider alternative medications'
            }
        
        # Check if med2 interacts with med1
        if med2_lower in interactions and med1_lower in interactions[med2_lower]:
            return {
                'medication1': med2,
                'medication2': med1,
                'interaction_type': 'drug_drug',
                'severity': 'moderate',
                'description': f"{med2} may interact with {med1}",
                'recommendation': 'Monitor closely and consider alternative medications'
            }
        
        return None
    
    def _check_contraindications(self, medication: str, drug_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check contraindications for a medication"""
        contraindications = drug_data.get("contraindications", {})
        med_lower = medication.lower()
        
        if med_lower in contraindications:
            return {
                'medication': medication,
                'contraindications': contraindications[med_lower],
                'severity': 'high',
                'description': f"{medication} has contraindications: {', '.join(contraindications[med_lower])}",
                'recommendation': 'Review contraindications before prescribing'
            }
        
        return None
    
    def _generate_recommendations(self, interactions: List[Dict], contraindications: List[Dict]) -> List[str]:
        """Generate recommendations based on interactions and contraindications"""
        recommendations = []
        
        if interactions:
            recommendations.append("Monitor for drug interactions and adjust dosages as needed")
            recommendations.append("Consider alternative medications if interactions are severe")
        
        if contraindications:
            recommendations.append("Review contraindications before prescribing")
            recommendations.append("Consider patient-specific risk factors")
        
        if not interactions and not contraindications:
            recommendations.append("No known interactions or contraindications identified")
        
        return recommendations

class MedicalCodeLookupTool(BaseTool):
    """Tool for looking up medical codes"""
    name: str = "lookup_medical_code"
    description: str = "Look up medical codes (ICD-10, CPT, etc.) and their descriptions"
    args_schema: type[BaseModel] = MedicalCodeInput
    
    def _run(self, code: str, code_type: str) -> Dict[str, Any]:
        """Look up medical code"""
        try:
            # Load medical code data
            code_data = self._load_medical_codes()
            
            code_upper = code.upper()
            code_type_lower = code_type.lower()
            
            if code_type_lower not in code_data:
                return {
                    'error': f"Unsupported code type: {code_type}",
                    'supported_types': list(code_data.keys())
                }
            
            # Search for the code
            codes = code_data[code_type_lower]
            
            # Exact match
            if code_upper in codes:
                return {
                    'code': code_upper,
                    'code_type': code_type,
                    'description': codes[code_upper],
                    'match_type': 'exact'
                }
            
            # Partial match
            partial_matches = []
            for c, desc in codes.items():
                if code_upper in c or c in code_upper:
                    partial_matches.append({
                        'code': c,
                        'description': desc
                    })
            
            if partial_matches:
                return {
                    'code': code_upper,
                    'code_type': code_type,
                    'partial_matches': partial_matches,
                    'match_type': 'partial'
                }
            
            return {
                'code': code_upper,
                'code_type': code_type,
                'error': 'Code not found',
                'match_type': 'none'
            }
            
        except Exception as e:
            logging.error(f"Medical code lookup failed: {str(e)}")
            return {
                'error': f"Medical code lookup failed: {str(e)}",
                'code': code,
                'code_type': code_type
            }
    
    def _load_medical_codes(self) -> Dict[str, Dict[str, str]]:
        """Load medical code data from JSON file"""
        try:
            data_file = Path(__file__).parent.parent.parent / "data" / "medical_codes.json"
            if data_file.exists():
                with open(data_file, 'r') as f:
                    return json.load(f)
            else:
                # Return basic medical codes if file doesn't exist
                return self._get_basic_medical_codes()
        except Exception as e:
            logging.error(f"Failed to load medical codes: {str(e)}")
            return self._get_basic_medical_codes()
    
    def _get_basic_medical_codes(self) -> Dict[str, Dict[str, str]]:
        """Get basic medical code data"""
        return {
            "icd10": {
                "I10": "Essential (primary) hypertension",
                "E11.9": "Type 2 diabetes mellitus without complications",
                "J45.909": "Unspecified asthma with (acute) exacerbation",
                "E78.5": "Disorder of lipoprotein metabolism, unspecified",
                "Z91.010": "Allergy to peanuts",
                "R50.9": "Fever, unspecified",
                "R07.9": "Chest pain, unspecified",
                "R06.02": "Shortness of breath"
            },
            "cpt": {
                "99213": "Office/outpatient visit established patient, 20-29 minutes",
                "99214": "Office/outpatient visit established patient, 30-39 minutes",
                "99215": "Office/outpatient visit established patient, 40-54 minutes",
                "99203": "Office/outpatient visit new patient, 30-44 minutes",
                "99204": "Office/outpatient visit new patient, 45-59 minutes",
                "99205": "Office/outpatient visit new patient, 60-74 minutes"
            }
        }

class SymptomAnalysisTool(BaseTool):
    """Tool for analyzing symptoms and suggesting possible conditions"""
    name: str = "analyze_symptoms"
    description: str = "Analyze patient symptoms and suggest possible conditions"
    args_schema: type[BaseModel] = SymptomAnalysisInput
    
    def _run(self, symptoms: List[str], patient_age: Optional[int] = None, patient_gender: Optional[str] = None) -> Dict[str, Any]:
        """Analyze symptoms and suggest conditions"""
        try:
            # Load symptom data
            symptom_data = self._load_symptom_data()
            
            # Analyze symptoms
            possible_conditions = []
            severity_assessment = "low"
            recommendations = []
            
            for symptom in symptoms:
                symptom_lower = symptom.lower()
                
                # Find matching conditions
                for condition, data in symptom_data.items():
                    if symptom_lower in data.get("symptoms", []):
                        possible_conditions.append({
                            'condition': condition,
                            'description': data.get("description", ""),
                            'severity': data.get("severity", "low"),
                            'matching_symptoms': [symptom]
                        })
            
            # Remove duplicates and sort by severity
            unique_conditions = {}
            for condition in possible_conditions:
                cond_name = condition['condition']
                if cond_name not in unique_conditions:
                    unique_conditions[cond_name] = condition
                else:
                    unique_conditions[cond_name]['matching_symptoms'].extend(condition['matching_symptoms'])
            
            possible_conditions = list(unique_conditions.values())
            
            # Assess overall severity
            if possible_conditions:
                severities = [c['severity'] for c in possible_conditions]
                if 'critical' in severities:
                    severity_assessment = "critical"
                elif 'high' in severities:
                    severity_assessment = "high"
                elif 'moderate' in severities:
                    severity_assessment = "moderate"
            
            # Generate recommendations
            if severity_assessment in ["critical", "high"]:
                recommendations.append("Seek immediate medical attention")
                recommendations.append("Consider emergency department evaluation")
            elif severity_assessment == "moderate":
                recommendations.append("Schedule appointment with healthcare provider")
                recommendations.append("Monitor symptoms closely")
            else:
                recommendations.append("Consider scheduling routine appointment")
                recommendations.append("Monitor for symptom changes")
            
            return {
                'symptoms': symptoms,
                'patient_age': patient_age,
                'patient_gender': patient_gender,
                'possible_conditions': possible_conditions,
                'severity_assessment': severity_assessment,
                'recommendations': recommendations,
                'total_conditions_found': len(possible_conditions)
            }
            
        except Exception as e:
            logging.error(f"Symptom analysis failed: {str(e)}")
            return {
                'error': f"Symptom analysis failed: {str(e)}",
                'symptoms': symptoms,
                'possible_conditions': [],
                'severity_assessment': 'unknown',
                'recommendations': ['Consult with healthcare provider']
            }
    
    def _load_symptom_data(self) -> Dict[str, Any]:
        """Load symptom data from JSON file"""
        try:
            data_file = Path(__file__).parent.parent.parent / "data" / "synthetic_patients.json"
            if data_file.exists():
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    # Extract condition data if available
                    return data.get("conditions", self._get_basic_symptom_data())
            else:
                return self._get_basic_symptom_data()
        except Exception as e:
            logging.error(f"Failed to load symptom data: {str(e)}")
            return self._get_basic_symptom_data()
    
    def _get_basic_symptom_data(self) -> Dict[str, Any]:
        """Get basic symptom data"""
        return {
            "hypertension": {
                "description": "High blood pressure",
                "symptoms": ["headache", "chest pain", "shortness of breath", "dizziness"],
                "severity": "moderate"
            },
            "diabetes": {
                "description": "Type 2 diabetes mellitus",
                "symptoms": ["frequent urination", "increased thirst", "fatigue", "blurred vision"],
                "severity": "moderate"
            },
            "asthma": {
                "description": "Chronic respiratory condition",
                "symptoms": ["wheezing", "shortness of breath", "chest tightness", "coughing"],
                "severity": "moderate"
            },
            "heart attack": {
                "description": "Myocardial infarction",
                "symptoms": ["chest pain", "shortness of breath", "nausea", "sweating"],
                "severity": "critical"
            },
            "pneumonia": {
                "description": "Lung infection",
                "symptoms": ["fever", "cough", "shortness of breath", "chest pain"],
                "severity": "high"
            }
        }

class VitalSignsAnalysisTool(BaseTool):
    """Tool for analyzing vital signs and identifying abnormalities"""
    name: str = "analyze_vital_signs"
    description: str = "Analyze patient vital signs and identify abnormalities"
    
    def _run(self, vital_signs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze vital signs for abnormalities"""
        try:
            abnormalities = []
            severity = "normal"
            recommendations = []
            
            # Define normal ranges
            normal_ranges = {
                'heart_rate': {'min': 60, 'max': 100},
                'systolic_bp': {'min': 90, 'max': 140},
                'diastolic_bp': {'min': 60, 'max': 90},
                'temperature': {'min': 97.0, 'max': 99.5},
                'oxygen_saturation': {'min': 95.0, 'max': 100.0},
                'respiratory_rate': {'min': 12, 'max': 20},
                'blood_glucose': {'min': 70, 'max': 140}
            }
            
            # Check each vital sign
            for vital, value in vital_signs.items():
                if vital in normal_ranges and value is not None:
                    ranges = normal_ranges[vital]
                    
                    if value < ranges['min']:
                        abnormalities.append({
                            'vital_sign': vital,
                            'value': value,
                            'status': 'low',
                            'normal_range': f"{ranges['min']}-{ranges['max']}",
                            'severity': self._assess_vital_severity(vital, value, 'low')
                        })
                    elif value > ranges['max']:
                        abnormalities.append({
                            'vital_sign': vital,
                            'value': value,
                            'status': 'high',
                            'normal_range': f"{ranges['min']}-{ranges['max']}",
                            'severity': self._assess_vital_severity(vital, value, 'high')
                        })
            
            # Assess overall severity
            if abnormalities:
                severities = [ab['severity'] for ab in abnormalities]
                if 'critical' in severities:
                    severity = "critical"
                elif 'high' in severities:
                    severity = "high"
                elif 'moderate' in severities:
                    severity = "moderate"
                else:
                    severity = "low"
            
            # Generate recommendations
            if severity == "critical":
                recommendations.append("Immediate medical attention required")
                recommendations.append("Consider emergency response")
            elif severity == "high":
                recommendations.append("Urgent medical evaluation needed")
                recommendations.append("Monitor closely")
            elif severity == "moderate":
                recommendations.append("Schedule medical appointment")
                recommendations.append("Continue monitoring")
            else:
                recommendations.append("Vital signs within normal range")
                recommendations.append("Continue routine monitoring")
            
            return {
                'vital_signs': vital_signs,
                'abnormalities': abnormalities,
                'overall_severity': severity,
                'recommendations': recommendations,
                'abnormal_count': len(abnormalities)
            }
            
        except Exception as e:
            logging.error(f"Vital signs analysis failed: {str(e)}")
            return {
                'error': f"Vital signs analysis failed: {str(e)}",
                'vital_signs': vital_signs,
                'abnormalities': [],
                'overall_severity': 'unknown'
            }
    
    def _assess_vital_severity(self, vital: str, value: float, status: str) -> str:
        """Assess severity of vital sign abnormality"""
        # Define severity thresholds for each vital sign
        severity_thresholds = {
            'heart_rate': {
                'low': {'moderate': 50, 'high': 40, 'critical': 30},
                'high': {'moderate': 110, 'high': 130, 'critical': 150}
            },
            'systolic_bp': {
                'low': {'moderate': 80, 'high': 70, 'critical': 60},
                'high': {'moderate': 160, 'high': 180, 'critical': 200}
            },
            'diastolic_bp': {
                'low': {'moderate': 50, 'high': 40, 'critical': 30},
                'high': {'moderate': 100, 'high': 110, 'critical': 120}
            },
            'temperature': {
                'low': {'moderate': 96.0, 'high': 95.0, 'critical': 94.0},
                'high': {'moderate': 100.5, 'high': 102.0, 'critical': 104.0}
            },
            'oxygen_saturation': {
                'low': {'moderate': 92, 'high': 90, 'critical': 88},
                'high': {'moderate': 100, 'high': 100, 'critical': 100}
            }
        }
        
        if vital in severity_thresholds and status in severity_thresholds[vital]:
            thresholds = severity_thresholds[vital][status]
            
            if status == 'low':
                if value <= thresholds['critical']:
                    return 'critical'
                elif value <= thresholds['high']:
                    return 'high'
                elif value <= thresholds['moderate']:
                    return 'moderate'
            else:  # high
                if value >= thresholds['critical']:
                    return 'critical'
                elif value >= thresholds['high']:
                    return 'high'
                elif value >= thresholds['moderate']:
                    return 'moderate'
        
        return 'low'
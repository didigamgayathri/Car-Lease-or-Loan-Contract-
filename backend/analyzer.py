"""
Contract Analyzer Module
Analyzes car lease/loan contracts and provides fairness scores, risk detection, and negotiation tips.
"""

import re
from typing import Dict, List, Any


class ContractAnalyzer:
    """Analyzes car lease/loan contracts using simple AI logic."""
    
    # Market averages for comparison
    MARKET_AVG_APR = 5.0  # 5% APR
    MARKET_MAX_APR = 7.0  # 7% is considered high
    STANDARD_MILEAGE = 12000
    STANDARD_LEASE_DURATION = 36
    
    def __init__(self):
        self.extracted_data = {}
        
    def extract_contract_info(self, text: str) -> Dict[str, Any]:
        """Extract key information from contract text."""
        text = text.lower()
        
        # Extract lease duration
        duration = self._extract_duration(text)
        
        # Extract monthly payment
        monthly_payment = self._extract_monthly_payment(text)
        
        # Extract mileage limit
        mileage_limit = self._extract_mileage(text)
        
        # Extract APR
        apr = self._extract_apr(text)
        
        # Check for early termination clause
        early_termination = self._check_early_termination(text)
        
        # Check for hidden fees
        hidden_fees = self._check_hidden_fees(text)
        
        return {
            "lease_duration": duration,
            "monthly_payment": monthly_payment,
            "mileage_limit": mileage_limit,
            "apr": apr,
            "early_termination": early_termination,
            "hidden_fees": hidden_fees
        }
    
    def _extract_duration(self, text: str) -> str:
        """Extract lease duration from text."""
        # Look for patterns like "36 months", "24 months", "3 years"
        patterns = [
            r'(\d+)\s*(?:month|months)\s*(?:term|lease|duration)?',
            r'(?:term|lease|duration)\s*(?:of)?\s*(\d+)\s*(?:month|months)',
            r'(\d+)\s*(?:year|years)\s*(?:term|lease)?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                months = int(match.group(1))
                if months > 12:  # If it's in months
                    return f"{months} months"
                else:  # If it's in years
                    return f"{months * 12} months"
        
        # Default if not found
        return "36 months"
    
    def _extract_monthly_payment(self, text: str) -> str:
        """Extract monthly payment from text."""
        patterns = [
            r'(?:monthly|per month|payment|due)\s*(?:of)?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:per|/)\s*month',
            r'(?:total|amount)\s*(?:due|payable)\s*(?:each|per)?\s*(?:month)?\s*:?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                amount = match.group(1).replace(',', '')
                return f"${float(amount):,.2f}"
        
        # Default if not found
        return "$0.00"
    
    def _extract_mileage(self, text: str) -> str:
        """Extract mileage limit from text."""
        patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*(?:mile|miles|mi)\s*(?:per|per\s*year|/yr)?',
            r'(?:annual|yearly)\s*(?:mileage|miles|limit)\s*(?:of)?\s*(\d{1,3}(?:,\d{3})*)',
            r'(?:mileage|miles)\s*limit\s*(?:of)?\s*(\d{1,3}(?:,\d{3})*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                mileage = match.group(1).replace(',', '')
                return f"{int(mileage):,} miles"
        
        # Default if not found
        return "12,000 miles"
    
    def _extract_apr(self, text: str) -> str:
        """Extract APR from text."""
        patterns = [
            r'(?:apr|annual\s*percentage\s*rate|interest\s*rate)\s*(?:of)?\s*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s*(?:apr|annual\s*percentage\s*rate)',
            r'(?:rate)\s*:?\s*(\d+(?:\.\d+)?)\s*%',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"{float(match.group(1))}%"
        
        # Default if not found
        return "0%"
    
    def _check_early_termination(self, text: str) -> bool:
        """Check for early termination clause."""
        patterns = [
            r'early\s*(?:termination|termination\s*fee|buyout)',
            r'termination\s*(?:fee|penalty|charge)',
            r'early\s*return',
            r'early\s*end\s*(?:of|to)\s*lease',
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _check_hidden_fees(self, text: str) -> List[str]:
        """Check for hidden fees."""
        fees = []
        
        fee_patterns = [
            (r'disposition\s*fee', 'Disposition fee'),
            (r'acquisition\s*fee', 'Acquisition fee'),
            (r'documentation\s*fee', 'Documentation fee'),
            (r'processing\s*fee', 'Processing fee'),
            (r'registration\s*fee', 'Registration fee'),
            (r'prep\s*fee', 'Preparation fee'),
            (r'administration\s*fee', 'Administration fee'),
            (r'security\s*deposit', 'Security deposit'),
            (r'excess\s*(?:mileage|wear)', 'Excess mileage/wear charge'),
        ]
        
        for pattern, name in fee_patterns:
            if re.search(pattern, text):
                fees.append(name)
        
        return fees
    
    def calculate_fairness_score(self, contract_info: Dict[str, Any]) -> int:
        """Calculate fairness score (0-100) based on contract terms."""
        score = 100
        
        # APR scoring (most important factor)
        apr_str = contract_info.get("apr", "0%").replace("%", "").strip()
        try:
            apr = float(apr_str)
            if apr > self.MARKET_MAX_APR:
                score -= (apr - self.MARKET_MAX_APR) * 5  # Heavy penalty for high APR
            elif apr > self.MARKET_AVG_APR:
                score -= (apr - self.MARKET_AVG_APR) * 3
        except ValueError:
            pass
        
        # Mileage limit scoring
        mileage_str = contract_info.get("mileage_limit", "0").replace(",", "").replace(" miles", "").strip()
        try:
            mileage = int(mileage_str)
            if mileage < 10000:
                score -= 20
            elif mileage < 12000:
                score -= 10
        except ValueError:
            pass
        
        # Lease duration scoring
        duration_str = contract_info.get("lease_duration", "0").replace(" months", "").strip()
        try:
            duration = int(duration_str)
            if duration > 48:
                score -= 15
            elif duration > 36:
                score -= 5
        except ValueError:
            pass
        
        # Early termination penalty
        if contract_info.get("early_termination"):
            score -= 10
        
        # Hidden fees
        if contract_info.get("hidden_fees"):
            score -= len(contract_info.get("hidden_fees", [])) * 5
        
        return max(0, min(100, int(score)))
    
    def calculate_risk_score(self, contract_info: Dict[str, Any]) -> int:
        """Calculate risk score (0-100) based on contract terms."""
        risk = 0
        
        # APR risk
        apr_str = contract_info.get("apr", "0%").replace("%", "").strip()
        try:
            apr = float(apr_str)
            if apr > 10:
                risk += 40
            elif apr > 7:
                risk += 25
            elif apr > self.MARKET_AVG_APR:
                risk += 10
        except ValueError:
            pass
        
        # Mileage limit risk
        mileage_str = contract_info.get("mileage_limit", "0").replace(",", "").replace(" miles", "").strip()
        try:
            mileage = int(mileage_str)
            if mileage < 10000:
                risk += 25
            elif mileage < 12000:
                risk += 10
        except ValueError:
            pass
        
        # Lease duration risk
        duration_str = contract_info.get("lease_duration", "0").replace(" months", "").strip()
        try:
            duration = int(duration_str)
            if duration > 48:
                risk += 20
            elif duration > 36:
                risk += 10
        except ValueError:
            pass
        
        # Early termination risk
        if contract_info.get("early_termination"):
            risk += 15
        
        # Hidden fees risk
        if contract_info.get("hidden_fees"):
            risk += len(contract_info.get("hidden_fees", [])) * 8
        
        return max(0, min(100, int(risk)))
    
    def get_risk_rating(self, risk_score: int) -> str:
        """Get risk rating based on risk score."""
        if risk_score <= 30:
            return "Low Risk"
        elif risk_score <= 60:
            return "Medium Risk"
        else:
            return "High Risk"
    
    def detect_risks(self, contract_info: Dict[str, Any]) -> List[str]:
        """Detect and list specific risks in the contract."""
        risks = []
        
        # APR risks
        apr_str = contract_info.get("apr", "0%").replace("%", "").strip()
        try:
            apr = float(apr_str)
            if apr > self.MARKET_MAX_APR:
                risks.append(f"High APR compared to market ({apr}% vs {self.MARKET_AVG_APR}% average)")
            elif apr > self.MARKET_AVG_APR:
                risks.append(f"APR above market average ({apr}% vs {self.MARKET_AVG_APR}% average)")
        except ValueError:
            pass
        
        # Mileage limit risks
        mileage_str = contract_info.get("mileage_limit", "0").replace(",", "").replace(" miles", "").strip()
        try:
            mileage = int(mileage_str)
            if mileage < 10000:
                risks.append(f"Very low mileage limit ({mileage:,} miles/year)")
            elif mileage < 12000:
                risks.append(f"Below standard mileage limit ({mileage:,} miles/year)")
        except ValueError:
            pass
        
        # Lease duration risks
        duration_str = contract_info.get("lease_duration", "0").replace(" months", "").strip()
        try:
            duration = int(duration_str)
            if duration > 48:
                risks.append(f"Very long lease duration ({duration} months)")
            elif duration > 36:
                risks.append(f"Extended lease duration ({duration} months)")
        except ValueError:
            pass
        
        # Early termination
        if contract_info.get("early_termination"):
            risks.append("Early termination penalty present")
        
        # Hidden fees
        hidden_fees = contract_info.get("hidden_fees", [])
        for fee in hidden_fees:
            risks.append(f"Potential hidden fee: {fee}")
        
        return risks
    
    def generate_negotiation_tips(self, contract_info: Dict[str, Any], risks: List[str]) -> List[str]:
        """Generate negotiation tips based on detected risks."""
        tips = []
        
        # APR tips
        apr_str = contract_info.get("apr", "0%").replace("%", "").strip()
        try:
            apr = float(apr_str)
            if apr > self.MARKET_AVG_APR:
                tips.append("Try to negotiate APR below 5% (current market average)")
                if apr > 7:
                    tips.append("Request a significant APR reduction - current rate is very high")
        except ValueError:
            pass
        
        # Mileage tips
        mileage_str = contract_info.get("mileage_limit", "0").replace(",", "").replace(" miles", "").strip()
        try:
            mileage = int(mileage_str)
            if mileage < 15000:
                tips.append(f"Ask to increase mileage limit to at least 15,000 miles/year")
        except ValueError:
            pass
        
        # Duration tips
        duration_str = contract_info.get("lease_duration", "0").replace(" months", "").strip()
        try:
            duration = int(duration_str)
            if duration > 36:
                tips.append(f"Consider negotiating a shorter {duration - 12}-month lease for better terms")
        except ValueError:
            pass
        
        # Early termination tips
        if contract_info.get("early_termination"):
            tips.append("Request removal or reduction of early termination penalty")
        
        # General tips
        if not tips:
            tips.append("Current terms appear reasonable - focus on getting any waived fees")
        
        tips.append("Ask dealer to waive acquisition and documentation fees")
        tips.append("Negotiate the capitalized cost (vehicle price) before discussing monthly payment")
        
        return tips
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Perform complete contract analysis."""
        # Extract contract information
        contract_info = self.extract_contract_info(text)
        
        # Calculate scores
        fairness_score = self.calculate_fairness_score(contract_info)
        risk_score = self.calculate_risk_score(contract_info)
        risk_rating = self.get_risk_rating(risk_score)
        
        # Detect risks
        risks = self.detect_risks(contract_info)
        
        # Generate negotiation tips
        negotiation_tips = self.generate_negotiation_tips(contract_info, risks)
        
        return {
            "lease_duration": contract_info["lease_duration"],
            "monthly_payment": contract_info["monthly_payment"],
            "mileage_limit": contract_info["mileage_limit"],
            "apr": contract_info["apr"],
            "fairness_score": fairness_score,
            "risk_score": risk_score,
            "risk_rating": risk_rating,
            "risks": risks,
            "negotiation_tips": negotiation_tips
        }


def analyze_contract(text: str) -> Dict[str, Any]:
    """Main function to analyze a contract."""
    analyzer = ContractAnalyzer()
    return analyzer.analyze(text)

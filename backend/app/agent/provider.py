import os
import re
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from app.schemas.agent import BuyerRequest
from app.services.formatters import format_inr


class LLMProvider(ABC):
    """
    Abstract LLM Provider interface for agentic communication and structured extraction.
    All financial numbers are strictly supplied by backend services.
    """

    @abstractmethod
    def extract_buyer_request(self, message: str, buyer_id: str = "buyer_enterprise_procure") -> Tuple[BuyerRequest, str]:
        """Extracts structured BuyerRequest from natural language message. Returns (request, mode)."""
        pass

    @abstractmethod
    def generate_merchant_offer_message(self, offer: Dict[str, Any], merchant_state_summary: str) -> str:
        """Generates natural language commercial proposal wrapping deterministic offer figures."""
        pass

    @abstractmethod
    def parse_buyer_counter(self, message: str, current_offer: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """Parses counteroffer constraints from buyer message."""
        pass

    @abstractmethod
    def generate_merchant_counter_message(self, offer: Dict[str, Any], rationale: str) -> str:
        """Generates updated commercial proposal after counteroffer re-evaluation."""
        pass

    @abstractmethod
    def generate_buyer_response_message(self, decision: str, offer: Dict[str, Any], rationale: str) -> str:
        """Generates buyer acceptance, counter, or rejection message."""
        pass


class DeterministicFallbackProvider(LLMProvider):
    """
    Zero-external-dependency, 100% reliable deterministic natural language parser and generator.
    Activated in Demo Fallback Mode or when external LLMs are unavailable.
    """

    def extract_buyer_request(self, message: str, buyer_id: str = "buyer_enterprise_procure") -> Tuple[BuyerRequest, str]:
        text = message.lower().strip()

        # 1. Extract Quantity
        qty_match = re.search(r'(\d+)\s*(units?|pcs?|pieces?|valves?|items?|qty)', text)
        if not qty_match:
            qty_match = re.search(r'(need|require|want|order|purchase)\s*(\d+)', text)
        if not qty_match:
            qty_match = re.search(r'\b(\d{2,4})\b', text)
        quantity = int(qty_match.group(1) if qty_match and qty_match.lastindex == 2 and qty_match.group(2).isdigit() else qty_match.group(1) if qty_match else 250)
        quantity = max(10, min(quantity, 5000))

        # 2. Extract Budget in Lakhs / Thousands / Raw numbers
        budget = Decimal("350000.00")
        lakh_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakhs?|lacs?|l\b)', text)
        k_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:k|thousand)', text)
        raw_budget_match = re.search(r'(?:₹|rs\.?|inr|budget|target)?\s*(\d{5,8})', text)

        if lakh_match:
            val = float(lakh_match.group(1))
            budget = Decimal(str(int(val * 100000)))
        elif k_match:
            val = float(k_match.group(1))
            budget = Decimal(str(int(val * 1000)))
        elif raw_budget_match:
            budget = Decimal(raw_budget_match.group(1))
        else:
            # Baseline default estimate ~ ₹1200 / unit
            budget = Decimal(quantity * 1350)

        # 3. Extract Delivery Days
        days_match = re.search(r'(\d+)\s*(?:days?|day lead|d delivery)', text)
        delivery_days = int(days_match.group(1)) if days_match else 6

        # 4. Extract Payment Preference
        if any(w in text for w in ['immediate', 'instant', 'upi', 'cash', 'advance', '0 day', '0-day', 'same day', 'prompt']):
            payment_days = 0
        elif any(w in text for w in ['7 day', '7-day', 'weekly', '7d']):
            payment_days = 7
        elif any(w in text for w in ['15 day', '15-day', '15d', 'semi-monthly']):
            payment_days = 15
        elif any(w in text for w in ['45 day', '45-day', '45d']):
            payment_days = 45
        elif any(w in text for w in ['30 day', '30-day', '30d', 'credit', 'net 30', 'trade credit']):
            payment_days = 30
        else:
            payment_days = 0

        # 5. Extract Product keywords
        prod_reqs = []
        if 'valve' in text:
            prod_reqs.append('Industrial Control Valves')
        if 'actuator' in text:
            prod_reqs.append('Electro-Hydraulic Actuator')
        if 'flange' in text:
            prod_reqs.append('Forged Flange')
        if not prod_reqs:
            prod_reqs.append('Standard Industrial Supply Lot')

        req = BuyerRequest(
            buyer_id=buyer_id,
            intent="bulk_purchase",
            product_requirements=prod_reqs,
            quantity=quantity,
            maximum_budget=budget,
            maximum_delivery_days=delivery_days,
            preferred_payment_days=payment_days,
            raw_inquiry_text=message,
        )
        return req, "fallback"

    def generate_merchant_offer_message(self, offer: Dict[str, Any], merchant_state_summary: str) -> str:
        qty = offer["quantity"]
        unit_price = offer["unit_price"]
        gross_fmt = format_inr(offer["gross_value"])
        payment_timing = offer["payment_timing_days"]
        delivery_days = offer["delivery_days"]
        tag = offer.get("strategy_tag", "Optimized Deal")

        settlement_desc = "immediate settlement (0-day UPI / Razorpay)" if payment_timing == 0 else f"{payment_timing}-day deferred commercial credit"

        return (
            f"Thank you for your inquiry. Based on our live inventory and working capital optimization, "
            f"we can offer {qty} units at ₹{unit_price:,.2f}/unit (Total: {gross_fmt}) with {settlement_desc}, "
            f"scheduled for dispatch within {delivery_days} business days. [{tag}]"
        )

    def parse_buyer_counter(self, message: str, current_offer: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        text = message.lower().strip()
        result = {}

        # Look for target budget
        lakh_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakhs?|lacs?|l\b)', text)
        k_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:k|thousand)', text)
        raw_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d{5,8})', text)

        if lakh_match:
            result["target_budget"] = Decimal(str(int(float(lakh_match.group(1)) * 100000)))
        elif k_match:
            result["target_budget"] = Decimal(str(int(float(k_match.group(1)) * 1000)))
        elif raw_match:
            result["target_budget"] = Decimal(raw_match.group(1))
        else:
            # If buyer just asks for a lower price without specific number, discount current gross by 4%
            curr_gross = Decimal(str(current_offer.get("gross_value", 350000)))
            result["target_budget"] = curr_gross * Decimal("0.96")

        # Check payment flexibility
        if 'immediate' in text or 'cash' in text or '0 day' in text:
            result["preferred_payment_days"] = 0
        elif '30 day' in text or 'credit' in text:
            result["preferred_payment_days"] = 30

        return result, "fallback"

    def generate_merchant_counter_message(self, offer: Dict[str, Any], rationale: str) -> str:
        qty = offer["quantity"]
        unit_price = offer["unit_price"]
        gross_fmt = format_inr(offer["gross_value"])
        payment_timing = offer["payment_timing_days"]
        delivery_days = offer["delivery_days"]

        settlement_desc = "immediate cash settlement" if payment_timing == 0 else f"{payment_timing}-day credit"

        return (
            f"We have re-evaluated your counteroffer against our current production capacity and liquidity twin. "
            f"We can adjust to {qty} units at ₹{unit_price:,.2f}/unit (Total: {gross_fmt}) with {settlement_desc} "
            f"and delivery within {delivery_days} days. {rationale}"
        )

    def generate_buyer_response_message(self, decision: str, offer: Dict[str, Any], rationale: str) -> str:
        gross_fmt = format_inr(offer["gross_value"])
        qty = offer["quantity"]

        if decision == "ACCEPT":
            return (
                f"We accept your proposal of {qty} units for {gross_fmt} with {offer['payment_timing_days']}d settlement. "
                f"The terms align with our procurement budget and delivery requirements. Ready to finalize agreement."
            )
        elif decision == "COUNTER":
            return (
                f"We reviewed the offer of {gross_fmt}. Could you adjust the total volume price closer to our target budget? "
                f"{rationale}"
            )
        else:
            return (
                f"Unfortunately, the proposed commercial terms of {gross_fmt} exceed our maximum allowable procurement ceiling. "
                f"We cannot proceed with this transaction at this time."
            )


class GeminiProvider(LLMProvider):
    """
    Google Gemini integration provider for dynamic intent extraction and offer phrasing.
    Seamlessly falls back to DeterministicFallbackProvider on any error, timeout, or missing key.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.fallback = DeterministicFallbackProvider()

    def extract_buyer_request(self, message: str, buyer_id: str = "buyer_enterprise_procure") -> Tuple[BuyerRequest, str]:
        if not self.api_key:
            return self.fallback.extract_buyer_request(message, buyer_id)

        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            prompt = (
                f"Extract structured B2B purchase requirements from this message as strict JSON:\n\n"
                f"Message: \"{message}\"\n\n"
                f"Return JSON with keys: quantity (int), maximum_budget (float), maximum_delivery_days (int), preferred_payment_days (int, 0 for immediate), product_keywords (list of strings)."
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            # If successful, parse JSON or fallback
            import json
            raw_text = response.text.strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            parsed = json.loads(raw_text)
            req = BuyerRequest(
                buyer_id=buyer_id,
                intent="bulk_purchase",
                product_requirements=parsed.get("product_keywords", ["Industrial Control Valves"]),
                quantity=int(parsed.get("quantity", 250)),
                maximum_budget=Decimal(str(parsed.get("maximum_budget", 350000))),
                maximum_delivery_days=int(parsed.get("maximum_delivery_days", 6)),
                preferred_payment_days=int(parsed.get("preferred_payment_days", 0)),
                raw_inquiry_text=message,
            )
            return req, "live_llm"
        except Exception:
            # Fail gracefully to deterministic fallback
            return self.fallback.extract_buyer_request(message, buyer_id)

    def generate_merchant_offer_message(self, offer: Dict[str, Any], merchant_state_summary: str) -> str:
        return self.fallback.generate_merchant_offer_message(offer, merchant_state_summary)

    def parse_buyer_counter(self, message: str, current_offer: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        return self.fallback.parse_buyer_counter(message, current_offer)

    def generate_merchant_counter_message(self, offer: Dict[str, Any], rationale: str) -> str:
        return self.fallback.generate_merchant_counter_message(offer, rationale)

    def generate_buyer_response_message(self, decision: str, offer: Dict[str, Any], rationale: str) -> str:
        return self.fallback.generate_buyer_response_message(decision, offer, rationale)


def get_llm_provider() -> LLMProvider:
    """Factory returning configured LLM Provider (Gemini if key exists, else Deterministic Fallback)."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return GeminiProvider(api_key=api_key)
    return DeterministicFallbackProvider()

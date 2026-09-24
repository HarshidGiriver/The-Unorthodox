"""Empathetic Outreach Agent: Disclosure-aware proactive borrower communication generator."""

from typing import Dict, Any, Optional
import datetime


from backend.config import (
    OPENAI_API_KEY,
    BANK_NAME,
    BANK_GRIEVANCE_OFFICER_NAME,
    BANK_GRIEVANCE_OFFICER_EMAIL,
    BANK_GRIEVANCE_OFFICER_PHONE,
    RBI_CALL_HOURS_START,
    RBI_CALL_HOURS_END,
)


class EmpatheticOutreachAgent:
    """Agent responsible for crafting empathetic, transparent, and Disclosure-aware restructuring offers."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY

    def is_within_rbi_contact_hours(self, current_time: Optional[datetime.time] = None) -> bool:
        """Verify if current time falls within RBI-permitted contact hours (08:00 to 19:00)."""
        from backend.communications import contact_window
        if current_time is not None:
            start = datetime.time.fromisoformat(RBI_CALL_HOURS_START)
            end = datetime.time.fromisoformat(RBI_CALL_HOURS_END)
            return start <= current_time < end
        return contact_window()

    def generate_outreach(
        self,
        customer_name: str,
        customer_id: str,
        restructuring_details: Dict[str, Any],
        language: str = "English",
        channel: str = "all",
    ) -> Dict[str, Any]:
        """Generate comprehensive, empathetic restructuring proposal outreach.

        Args:
            customer_name: Borrower full name.
            customer_id: Borrower account identifier.
            restructuring_details: Output from DebtRestructuringAgent.optimize_restructuring.
            language: Desired language ("English" or "Hindi").
            channel: Communication channel ("email", "sms", or "all").

        Returns:
            Dictionary containing email, sms, compliance disclosures, and metadata.
        """
        old_emi = restructuring_details.get("old_emi", 0.0)
        new_emi = restructuring_details.get("new_emi", 0.0)
        savings = restructuring_details.get("monthly_savings", 0.0)
        new_tenure = restructuring_details.get("new_tenure_months", 0)
        moratorium = restructuring_details.get("moratorium_months", 0)

        # Authoritative financial messages use deterministic templates only.
        email_body = self._generate_template_email(
            customer_name, customer_id, old_emi, new_emi, savings, new_tenure, moratorium, language
        )
        sms_body = self._generate_template_sms(customer_name, old_emi, new_emi, savings, language)
        disclosure = (
            f"\nAPR: {restructuring_details['new_annual_rate'] * 100:.2f}%. "
            f"Total interest: INR {restructuring_details['total_interest_new']:.2f}; "
            f"original: INR {restructuring_details['total_interest_old']:.2f}. "
            f"Interest-only payment: INR {restructuring_details['moratorium_payment']:.2f} "
            f"for {moratorium} months. Draft simulation; no approval or delivery has occurred."
        )
        email_body += disclosure
        sms_body += disclosure

        return {
            "customer_id": customer_id,
            "customer_name": customer_name,
            "language": language,
            "is_rbi_compliant_timing": self.is_within_rbi_contact_hours(),
            "email_subject": f"Flexible Payment Relief Options from {BANK_NAME}",
            "email_body": email_body,
            "sms_body": sms_body,
            "statutory_disclosures": {
                "bank_name": BANK_NAME,
                "grievance_officer": BANK_GRIEVANCE_OFFICER_NAME,
                "grievance_email": BANK_GRIEVANCE_OFFICER_EMAIL,
                "grievance_phone": BANK_GRIEVANCE_OFFICER_PHONE,
                "regulatory_framework": "Disclosure guidance; no regulatory certification claimed",
            },
        }

    def _generate_template_email(
        self,
        name: str,
        cust_id: str,
        old_emi: float,
        new_emi: float,
        savings: float,
        new_tenure: int,
        moratorium: int,
        language: str,
    ) -> str:
        """Generate structured email respecting RBI transparency guidelines."""
        moratorium_clause = (
            f"- Moratorium / Grace Period: {moratorium} months (no principal deduction)\n"
            if moratorium > 0
            else ""
        )

        if language.lower() == "hindi":
            return (
                f"प्रिय {name},\n\n"
                f"{BANK_NAME} में हम आपकी निरंतर वित्तीय भलाई को सर्वोच्च प्राथमिकता देते हैं।\n"
                f"हम समझते हैं कि जीवन में अनपेक्षित खर्च कभी-कभी नकदी प्रवाह को प्रभावित कर सकते हैं।\n"
                f"आपके ऋण खाते ({cust_id}) को सहज बनाए रखने के लिए, हमने एक अनुकूलित राहत योजना तैयार की है:\n\n"
                f"• वर्तमान ईएमआई: ₹{old_emi:,.2f}\n"
                f"• प्रस्तावित नई ईएमआई: ₹{new_emi:,.2f}\n"
                f"• मासिक बचत: ₹{savings:,.2f}\n"
                f"• संशोधित अवधि: {new_tenure} महीने\n"
                f"{moratorium_clause}\n"
                f"यह एक स्वैच्छिक सहायता प्रस्ताव है। इसे स्वीकार करने के लिए आप फिनसेफ पोर्टल पर लॉगिन कर सकते हैं।\n\n"
                f"आरबीआई निष्पक्ष आचरण संहिता के अनुसार, किसी भी प्रश्न के लिए हमारे शिकायत निवारण अधिकारी "
                f"{BANK_GRIEVANCE_OFFICER_NAME} से {BANK_GRIEVANCE_OFFICER_PHONE} पर संपर्क करें।\n\n"
                f"सादर,\n{BANK_NAME}"
            )

        return (
            f"Dear {name},\n\n"
            f"At {BANK_NAME}, your long-term financial peace of mind is our priority. We recognize that occasional "
            f"cash flow fluctuations and unplanned expenses happen to everyone.\n\n"
            f"To support your continued financial comfort, we have reviewed your account ({cust_id}) and prepared a simulated preview of "
            f"a proactive debt restructuring plan designed to lower your monthly outflow:\n\n"
            f"  • Current Monthly EMI: ₹{old_emi:,.2f}\n"
            f"  • Restructured Monthly EMI: ₹{new_emi:,.2f}\n"
            f"  • Immediate Monthly Cash Flow Relief: ₹{savings:,.2f}\n"
            f"  • Revised Loan Tenure: {new_tenure} months\n"
            f"{moratorium_clause}\n"
            f"This restructuring offer is completely voluntary and intended solely to assist you in maintaining a "
            f"healthy credit profile without distress.\n\n"
            f"To review full terms, transparent amortisation schedules, and review the proposed schedule, "
            f"please visit your Kintsugi Customer Portal.\n\n"
            f"Statutory Notice (RBI Fair Practices Code):\n"
            f"For any queries or grievances, please reach our dedicated Grievance Redressal Officer:\n"
            f"{BANK_GRIEVANCE_OFFICER_NAME} | Email: {BANK_GRIEVANCE_OFFICER_EMAIL} | Helpline: {BANK_GRIEVANCE_OFFICER_PHONE}\n\n"
            f"Warm regards,\n"
            f"Customer Care & Credit Solutions Group\n"
            f"{BANK_NAME}"
        )

    def _generate_template_sms(
        self,
        name: str,
        old_emi: float,
        new_emi: float,
        savings: float,
        language: str,
    ) -> str:
        """Generate concise SMS notification conforming to TRAI/RBI norms."""
        if language.lower() == "hindi":
            return (
                f"{BANK_NAME}: प्रिय {name}, आपके ऋण के लिए राहत योजना उपलब्ध है। "
                f"अपनी ईएमआई को ₹{old_emi:,.0f} से घटाकर ₹{new_emi:,.0f} करें (मासिक बचत: ₹{savings:,.0f})। "
                f"विवरण देखने व स्वीकृति हेतु फिनसेफ ऐप खोलें। हेल्पलाइन: {BANK_GRIEVANCE_OFFICER_PHONE}"
            )
        return (
            f"{BANK_NAME}: Hi {name}, proactive financial relief is available for your loan. "
            f"Reduce your EMI from ₹{old_emi:,.0f} to ₹{new_emi:,.0f} (save ₹{savings:,.0f}/month). "
            f"Check terms & accept via the Kintsugi portal. Toll-Free: {BANK_GRIEVANCE_OFFICER_PHONE}"
        )

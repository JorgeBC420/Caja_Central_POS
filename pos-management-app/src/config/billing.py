from dataclasses import dataclass

@dataclass
class BillingConfig:
    tax_rate: float
    invoice_format: str
    currency: str

billing_config = BillingConfig(
    tax_rate=0.15,  # Example tax rate of 15%
    invoice_format="PDF",  # Example invoice format
    currency="USD"  # Example currency
)
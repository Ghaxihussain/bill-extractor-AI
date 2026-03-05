from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Optional
from currency_converter import CurrencyConverter
from pydantic import BaseModel
import json
import time
import re

load_dotenv()

client = OpenAI()
c = CurrencyConverter()



class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: float
    total: float


class Invoice(BaseModel):
    vendor: str
    invoice_number: str
    date: str
    line_items: List[LineItem]
    total: float
    currency: str
    notes: Optional[str] = None



def convert(usd_amount: float) -> float:
    return c.convert(usd_amount, "USD", "EUR")


def calculate_total(numbers: List[float]) -> float:
    return sum(numbers)


def valid_vat(VAT_number: str) -> dict:

    patterns = {
        "DE": r"^DE\d{9}$",
        "GB": r"^GB\d{9}$",
        "FR": r"^FR[A-Z0-9]{2}\d{9}$",
        "NL": r"^NL\d{9}B\d{2}$",
        "IT": r"^IT\d{11}$",
    }

    prefix = VAT_number[:2]
    pattern = patterns.get(prefix)

    if not pattern:
        return {"valid": False, "reason": f"Unknown country: {prefix}"}

    is_valid = bool(re.match(pattern, VAT_number))

    return {
        "valid": is_valid,
        "reason": "Valid" if is_valid else "Invalid format"
    }


tool_functions = {
    "convert": convert,
    "calculate_total": calculate_total,
    "valid_vat": valid_vat,
}

with open("tools.json", "r") as j:
    tools = json.load(j)

print(tools)

messages = [
    {
        "role": "system",
        "content": """
You are an invoice processing assistant.

Use tools when needed:
- validate VAT numbers
- calculate totals
- convert currencies

Think step by step.
"""
    },
    {
        "role": "user",
        "content": """
Invoice #1042
From: Acme Software GmbH
Date: 2nd March 2026
VAT: DE123456789

Web hosting x3 months     $150.00
API usage fees             $89.50
Setup fee                  $200.00

Subtotal: $439.50
Tax (19%): $83.50
Total: $523.00

Please pay in EUR.
"""
    }
]


response = client.chat.completions.create(
    model="gpt-4o-mini",
    temperature=0,
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

message = response.choices[0].message
finish_reason = response.choices[0].finish_reason

messages.append(message)

if finish_reason == "tool_calls":
    for tool_call in message.tool_calls:
        
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        print(f"\nTool called: {name}")
        print("Arguments:", args)

        result = tool_functions[name](**args)

        print("Result:", result)

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result)
        })

    




structured = client.chat.completions.parse(
    model="gpt-4o-mini",
    temperature=0,
    messages=messages,
    response_format=Invoice
)

invoice = structured.choices[0].message.parsed

print("\nFINAL STRUCTURED INVOICE\n")
print(invoice.model_dump_json(indent=2))

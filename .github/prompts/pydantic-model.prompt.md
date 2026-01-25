---
description: 'Generate pydantic validation models for API responses'
mode: 'agent'
---

# Pydantic Model Generator

Generate Pydantic v2 models for API response validation:

## Model Template

```python
from pydantic import BaseModel, Field, field_validator
from typing import Any

class ItemPrice(BaseModel):
    """Price information for a market item."""
    
    usd: int = Field(description="Price in USD cents")
    dmc: int = Field(default=0, description="Price in DMC tokens")
    
    @property
    def usd_dollars(self) -> float:
        """Convert cents to dollars."""
        return self.usd / 100

class MarketItem(BaseModel):
    """DMarket item from API response."""
    
    item_id: str = Field(alias="itemId")
    title: str
    price: ItemPrice
    game_id: str = Field(alias="gameId")
    
    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v
    
    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }
```

## Rules

- Use Pydantic v2 syntax
- Add Field descriptions for all fields
- Use alias for camelCase API fields
- Add validators for business logic
- Configure extra="ignore" for forward compatibility

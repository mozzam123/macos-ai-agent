from pydantic import BaseModel, Field


class CommandIntent(BaseModel):
    action: str = Field(description="The action the user wants to perform.")

    target: str = Field(description="The target of the action.")

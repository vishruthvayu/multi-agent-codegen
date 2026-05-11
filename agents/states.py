from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class File(BaseModel):
    path: str = Field(description="The path to the file to be created or modified")
    purpose: str = Field(description="Purpose of the file")


class Plan(BaseModel):
    name: str = Field(description="The name of the application")
    description: str = Field(description="One line application description")
    tech_stack: list[str] = Field(description="Technologies used in the project")
    features: list[str] = Field(description="List of project features")
    files: list[File] = Field(description="List of files required for the project")


class ImplementationTask(BaseModel):
    filepath: str = Field(description="Path to the file")
    task_description: str = Field(description="Detailed implementation instructions for this file")


class TaskPlan(BaseModel):
    implementation_steps: list[ImplementationTask] = Field(description="Ordered implementation steps")
    model_config = ConfigDict(extra="allow")


class CoderState(BaseModel):
    task_plan: TaskPlan = Field(description="Implementation task plan")
    current_step_idx: int = Field(0, description="Current implementation step index")
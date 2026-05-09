from pydantic import BaseModel,Field,ConfigDict
from typing import Optional

class File(BaseModel):
    path : str = Field(description="The path to the file to be created or modified ")
    purpose : str = Field(description="the purpose of the file to be created. eg: 'main application logic','data processing models',etc")

class Plan(BaseModel):
    name : str = Field(description="the name of the app to be build")
    description : str = Field(description="a one line description of the app to be build eg: a simple application to manage a persons finances")
    tech_stack : list[str] = Field(description="a list of technologies the app should be build with eg: ['react', 'node.js', 'mongodb','flask', 'python', 'docker', etc]")
    features : list[str] = Field(description="a list of features the app should have eg: ['a dashboard to view finances', 'a feature to add expenses', 'a feature to add income', etc]")
    files : list[File] = Field(description="a list of files to be created, each with a 'path' and 'purpose' ")

class ImplementationTask(BaseModel):
    filepath: str = Field(description="The path to the file to be modified")
    task_description: str = Field(description="A detailed description of the task to be performed on the file, e.g. 'add user authentication', 'implement data processing logic', etc.")
    operation: str = Field(description="overwrite or append")
    
class TaskPlan(BaseModel):
    implementation_steps: list[ImplementationTask] = Field(description="A list of steps to be taken to implement the task")
    model_config = ConfigDict(extra="allow")
    
class CoderState(BaseModel):
    task_plan: TaskPlan = Field(description="The plan for the task to be implemented")
    current_step_idx: int = Field(0, description="The index of the current step in the implementation steps")
    current_file_content: Optional[str] = Field(None, description="The content of the file currently being edited or created")
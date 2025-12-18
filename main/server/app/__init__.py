from fastapi import FastAPI

app = FastAPI()

# Import endpoints to register them
from . import main


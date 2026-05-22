from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.controllers.document_controller import DocumentController
from app.db.session import get_db
from app.services.document_service import DocumentService


def get_document_controller(db: Session = Depends(get_db)) -> DocumentController:
    return DocumentController(DocumentService(db))


DocumentControllerDep = Annotated[DocumentController, Depends(get_document_controller)]


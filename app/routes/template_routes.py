from fastapi import APIRouter, Depends, HTTPException
from app.pydantic_schemas import RenderRequest, RenderResponse, TemplateCreate, TemplateResponse
from app.database import get_db
from sqlalchemy.orm import Session
from app.models import Template
from typing import List
from app.utils import render_template

router = APIRouter()

#  POST /templates — create a template
@router.post("/", response_model=TemplateResponse)
def create_template(template: TemplateCreate, db: Session = Depends(get_db)):
    user_template = db.query(Template).filter(Template.name == template.name).first()
    if user_template:
        raise HTTPException(status_code=409, detail= "Template already exist")
    else:
        user_template = Template(name = template.name, 
                                 subject = template.subject,
                                 body = template.body, 
                                 channel = template.channel)
        db.add(user_template)
        db.commit()
        db.refresh(user_template)
        return user_template
# GET /templates — list all templates
@router.get("/", response_model=List[TemplateResponse])
def get_templates(db: Session = Depends(get_db)):
    templates = db.query(Template).all()
    return templates
# GET /templates/{template_id} — get one template
@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail= "Template not found")
    else:
        return template
# POST /templates/{template_id}/render — render a template with variables
@router.post("/{template_id}/render", response_model=RenderResponse)
def render(template_id: int, request: RenderRequest, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail= "Template not found")
    render_subject = None
    try:
    # render body
        render_body = render_template(template.body, request.variables)
    # render subject if it exists
        if template.subject:
            render_subject = render_template(template.subject, request.variables)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return RenderResponse(rendered_subject=render_subject, rendered_body=render_body)
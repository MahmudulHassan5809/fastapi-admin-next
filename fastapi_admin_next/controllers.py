from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_admin_next.db_connect import DBConnector
from fastapi_admin_next.dependencies import CommonQueryParam
from fastapi_admin_next.exceptions import ValidationException
from fastapi_admin_next.schemas import NotFoundResponse
from fastapi_admin_next.service import AdminNextService

router = APIRouter(prefix="")


service = AdminNextService()


@router.get("/", response_class=HTMLResponse)
async def admin_index(request: Request) -> Any:
    models = service.get_homepage()
    return service.templates.TemplateResponse(
        "index.html", {"request": request, "models": models}
    )


@router.get("/{model_name}/list", response_class=HTMLResponse, name="list_view")
async def list_view(
    request: Request,
    model_name: str,
    db: AsyncSession = Depends(DBConnector.dependency()),
) -> Any:
    model = next(
        (m for m in service.registry.get_models() if m.__name__ == model_name), None
    )
    if not model:
        raise ValidationException(message="Model not found")
    query_params = CommonQueryParam(
        filter_fields=service.registry.get_filter_fields(model=model)
    )(request=request)

    response = await service.get_list_view(
        model=model, query_params=query_params, db=db
    )

    return service.templates.TemplateResponse(
        "list.html",
        {
            "request": request,
            "model_name": model_name,
            "rows": response.rows,
            "columns": response.columns,
            "filter_options": response.filter_options,  # Pass filter options to template
            "query_params": query_params,
            "total": response.total,
            "models": response.models,
        },
    )


@router.get("/{model_name}/create", response_class=HTMLResponse)
async def create_form(
    request: Request,
    model_name: str,
    db: AsyncSession = Depends(DBConnector.dependency()),
) -> Any:
    model = next(
        (m for m in service.registry.get_models() if m.__name__ == model_name), None
    )
    if not model:
        return HTMLResponse(content="Model not found", status_code=404)

    response = await service.get_create_view(model=model, db=db)

    error_messages = request.session.get("errors", [])
    form_data = request.session.get("form_data", {})

    request.session.pop("errors", None)
    request.session.pop("form_data", None)

    return service.templates.TemplateResponse(
        "create.html",
        {
            "request": request,
            "model_name": model_name,
            "columns": response.columns,
            "related_options": response.related_options,
            "fk_to_rel_map": response.fk_to_rel_map,
            "enum_fields": response.enum_fields,
            "errors": error_messages,
            "form_data": form_data,
            "models": response.models,
        },
    )


@router.post("/{model_name}/create", response_class=HTMLResponse)
async def create_action(
    request: Request,
    model_name: str,
    db: AsyncSession = Depends(DBConnector.dependency()),
) -> Any:
    # Fetch the model from the registry
    model = next(
        (m for m in service.registry.get_models() if m.__name__ == model_name), None
    )
    if not model:
        return HTMLResponse(content="Model not found", status_code=404)

    form_data = await request.form()
    data_dict = {key: value or None for key, value in form_data.items()}
    response = await service.save_view(data_dict=data_dict, model=model, db=db)

    if response.errors:
        request.session["errors"] = response.errors
        request.session["form_data"] = {
            key: value for key, value in data_dict.items() if value is not None
        }
        return RedirectResponse(f"/admin/{model.__name__}/create", status_code=303)

    return RedirectResponse(f"/admin/{model_name}/list", status_code=303)


# Edit form
@router.get("/{model_name}/update/{obj_id}", response_class=HTMLResponse)
async def update_form(
    request: Request,
    model_name: str,
    obj_id: str,
    db: AsyncSession = Depends(DBConnector.dependency()),
) -> Any:
    model = next(
        (m for m in service.registry.get_models() if m.__name__ == model_name), None
    )
    if not model:
        return HTMLResponse(content="Model not found", status_code=404)
    response = await service.get_detail_view(model=model, obj_id=obj_id, db=db)

    if isinstance(response, NotFoundResponse):
        return HTMLResponse(content="Object not found", status_code=404)

    error_messages = request.session.get("errors", [])

    request.session.pop("errors", None)

    return service.templates.TemplateResponse(
        "update.html",
        {
            "request": request,
            "model_name": model_name,
            "row": response.row,
            "columns": response.columns,
            "foreign_keys": response.related_data,
            "enum_fields": response.enum_fields,
            "errors": error_messages,
            "models": response.models,
        },
    )


@router.post("/{model_name}/update/{obj_id}", response_class=HTMLResponse)
async def update_action(
    request: Request,
    model_name: str,
    obj_id: int,
    db: AsyncSession = Depends(DBConnector.dependency()),
) -> Any:
    model = next(
        (m for m in service.registry.get_models() if m.__name__ == model_name), None
    )
    if not model:
        return HTMLResponse(content="Model not found", status_code=404)

    form_data = await request.form()
    data_dict = {key: value or None for key, value in form_data.items()}
    response = await service.update_view(
        data_dict=data_dict,
        model=model,
        obj_id=obj_id,
        db=db,
    )

    if response.errors:
        request.session["errors"] = response.errors
        request.session["form_data"] = {
            key: value for key, value in data_dict.items() if value is not None
        }
        return RedirectResponse(f"/admin/{model_name}/update/{obj_id}", status_code=303)

    return RedirectResponse(f"/admin/{model_name}/list", status_code=303)

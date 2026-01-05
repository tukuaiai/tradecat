"""
REST 路由定义。

当前暴露健康检查、模板列表、示例渲染接口。
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.settings import Settings, get_settings
from templates.registry import TemplateMeta, register_defaults

router = APIRouter()
registry = register_defaults()


class RenderRequest(BaseModel):
    """渲染请求体。"""

    template_id: str = Field(..., description="模板标识，如 line-basic")
    params: Dict[str, Any] = Field(default_factory=dict, description="模板参数")
    output: str = Field("png", description="输出类型：png 或 json")


def require_token(
    settings: Settings = Depends(get_settings),
    token: str | None = Header(default=None, alias="X-Vis-Token"),
):
    """简易 Token 校验，未配置 token 时直接放行。"""

    if not settings.token:
        return settings
    if token != settings.token:
        raise HTTPException(status_code=401, detail="无效的访问令牌")
    return settings


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> Dict[str, str]:
    """健康检查。"""

    return {"status": "ok", "service": settings.service_name}


@router.get("/templates", response_model=List[TemplateMeta])
def list_templates() -> List[TemplateMeta]:
    """列出已注册模板。"""

    return list(registry.list())


@router.post("/render")
def render(req: RenderRequest, settings: Settings = Depends(require_token)):
    """渲染指定模板。"""

    meta_and_fn = registry.get(req.template_id)
    if not meta_and_fn:
        raise HTTPException(status_code=404, detail="模板不存在")

    meta, render_fn = meta_and_fn
    if req.output not in meta.outputs:
        raise HTTPException(status_code=400, detail=f"输出类型不支持: {req.output}")

    try:
        content, media_type = render_fn(req.params, req.output)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"渲染失败: {exc}") from exc

    if media_type == "application/json":
        return JSONResponse(content=content, media_type=media_type)

    return Response(content=content, media_type=media_type)

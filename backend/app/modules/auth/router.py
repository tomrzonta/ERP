"""Rotas de autenticação. Recebem, validam, chamam o service e confirmam."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NaoAutenticado
from app.modules.assinaturas import service as assinaturas_service
from app.modules.auth import service
from app.modules.auth.dependencias import (
    Autenticado,
    Contexto,
    obter_autenticado,
    obter_contexto,
)
from app.modules.auth.schemas import (
    AccessTokenSaida,
    CadastroEntrada,
    EmpresaAtivaEntrada,
    EmpresaDisponivelSaida,
    EmpresaSaida,
    EuSaida,
    LoginEntrada,
    LoginSaida,
    RenovarEntrada,
    TokensSaida,
    UsuarioSaida,
)
from app.modules.empresas import service as empresas_service
from app.modules.usuarios import service as usuarios_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _origem(request: Request) -> dict:
    return {
        "user_agent": request.headers.get("user-agent"),
        "ip": request.client.host if request.client else None,
    }


def _login_saida(resultado: service.ResultadoLogin) -> LoginSaida:
    return LoginSaida(
        tokens=TokensSaida(
            access_token=resultado.tokens.access_token,
            refresh_token=resultado.tokens.refresh_token,
        ),
        empresa_ativa_id=resultado.empresa_ativa_id,
        empresas=[EmpresaDisponivelSaida(**vars(e)) for e in resultado.empresas],
    )


@router.post("/cadastro", response_model=LoginSaida, status_code=status.HTTP_201_CREATED)
def cadastro(dados: CadastroEntrada, request: Request, db: Session = Depends(get_db)):
    resultado = service.cadastrar(
        db,
        nome=dados.nome,
        email=dados.email,
        senha=dados.senha,
        nome_empresa=dados.nome_empresa,
        **_origem(request),
    )
    db.commit()
    return _login_saida(resultado)


@router.post("/login", response_model=LoginSaida)
def login(dados: LoginEntrada, request: Request, db: Session = Depends(get_db)):
    resultado = service.login(db, email=dados.email, senha=dados.senha, **_origem(request))
    db.commit()
    return _login_saida(resultado)


@router.post("/renovar", response_model=TokensSaida)
def renovar(dados: RenovarEntrada, db: Session = Depends(get_db)):
    try:
        tokens = service.renovar(db, dados.refresh_token)
    except NaoAutenticado:
        # Confirma uma eventual revogação por reuso de token antes de responder
        db.commit()
        raise
    db.commit()
    return TokensSaida(access_token=tokens.access_token, refresh_token=tokens.refresh_token)


@router.get("/empresas", response_model=list[EmpresaDisponivelSaida])
def empresas(
    autenticado: Autenticado = Depends(obter_autenticado), db: Session = Depends(get_db)
):
    return [
        EmpresaDisponivelSaida(**vars(e))
        for e in service.empresas_disponiveis(db, autenticado.usuario_id)
    ]


@router.post("/empresa-ativa", response_model=AccessTokenSaida)
def empresa_ativa(
    dados: EmpresaAtivaEntrada,
    autenticado: Autenticado = Depends(obter_autenticado),
    db: Session = Depends(get_db),
):
    token = service.definir_empresa_ativa(
        db,
        usuario_id=autenticado.usuario_id,
        sessao_id=autenticado.sessao_id,
        empresa_id=dados.empresa_id,
    )
    db.commit()
    return AccessTokenSaida(access_token=token)


@router.get("/eu", response_model=EuSaida)
def eu(contexto: Contexto = Depends(obter_contexto), db: Session = Depends(get_db)):
    usuario = usuarios_service.por_id(db, contexto.usuario_id)
    empresa = empresas_service.por_id(db, contexto.empresa_id)
    plano = assinaturas_service.plano_efetivo(db, contexto.empresa_id)
    return EuSaida(
        usuario=UsuarioSaida(id=usuario.id, nome=usuario.nome, email=usuario.email),
        empresa=EmpresaSaida(id=empresa.id, nome=empresa.nome_fantasia, slug=empresa.slug),
        papel=contexto.papel_nome,
        permissoes=sorted(contexto.permissoes),
        plano=plano.codigo,
    )


@router.post("/sair", status_code=status.HTTP_204_NO_CONTENT)
def sair(autenticado: Autenticado = Depends(obter_autenticado), db: Session = Depends(get_db)):
    service.sair(db, autenticado.sessao_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/sair-de-todos", status_code=status.HTTP_204_NO_CONTENT)
def sair_de_todos(
    autenticado: Autenticado = Depends(obter_autenticado), db: Session = Depends(get_db)
):
    service.sair_de_todos(db, autenticado.usuario_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

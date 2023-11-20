from itertools import count
from typing import Optional
from flask import Flask, request, jsonify
from flask_pydantic_spec import FlaskPydanticSpec, Response, Request
from pydantic import BaseModel, Field
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage

server = Flask(__name__)
spec = FlaskPydanticSpec('flask', title='PetHappyAPI')
spec.register(server)  # registra os endpoints do servidor 'server'
database = TinyDB(storage=MemoryStorage)  # "persiste isso aqui pra mim num arquivo database.json"
c = count()


# Query para buscar um pet
class QueryPet(BaseModel):
    id: Optional[int]
    nome: Optional[str]
    raca: Optional[str]


class Pet(BaseModel):
    id: Optional[int] = Field(default_factory=lambda: next(c))
    nome: str
    raca: str


class Pets(BaseModel):
    pets: list[Pet]
    count: int


## -------->>   GET   <<--------
@server.get('/pets')  # _Rota, endpoint, recurso ...
@spec.validate(
    query=QueryPet,
    resp=Response(HTTP_200=Pets)
)
def buscar_pets():
    """Retorna todos os Pets da base de dados"""
    query = request.context.query.dict(exclude_none=True)
    todos_os_pets = database.search(
        Query().fragment(query)
    )
    return jsonify(
        Pets(
            pets=todos_os_pets,
            count=len(todos_os_pets)
        ).dict()
    )


## -------->>   GET para um único pet  <<--------
@server.get('/pets/<int:id>')  # _Rota, endpoint, recurso ...
@spec.validate(resp=Response(HTTP_200=Pet))
def buscar_pet(id):  ##  tem que especificar id., por isso '(id)'
    """Retorna um Pet da base de dados"""
    try:
        pet = database.search(Query().id == id)[0]
    except IndexError:
        return {'message': 'Pet not found'}, 404
    return jsonify(pet)


## -------->>   POST   <<--------
@server.post('/pets')
@spec.validate(body=Request(Pet),
               resp=Response(HTTP_200=Pet))  # 'HTTP_200=Pet' Lê-se que o OK dessa resposta 200 é a classe Pet
def inserir_pet():
    """Insere um Pet na base de dados"""
    body = request.context.body.dict()
    database.insert(body)  # insere um Pet no database
    return body


## -------->>   PUT   <<--------
@server.put('/pets/<int:id>')
@spec.validate(body=Request(Pet), resp=Response(HTTP_201=Pet))
def altera_pet(id):
    """Altera um Pet do banco de dados"""
    Pet = Query()  ## Pet é só uma variável pra deixar mais simples
    body = request.context.body.dict()
    database.update(body, Pet.id == id)
    # database.update(body, Query().id == id) << poderia ser assim, e sem o 'Pet = Query()' ali em cima
    return jsonify(body)


## -------->>   DELETE   <<--------
@server.delete('/pets/<int:id>')
@spec.validate(resp=Response('HTTP_204'))
def delete_pet(id):
    """Remove um Pet do banco de dados"""
    Pet = Query()  ## Pet é só uma variável pra deixar mais simples
    database.remove(Pet.id == id)  # Remove onde o Pet tiver o id igual a 'tal'
    return jsonify({})  # =====> POR DEFINIÇÃO, O DELETE NÃO RETORNA NADA. POR ISSO USA-SE {}


server.run()

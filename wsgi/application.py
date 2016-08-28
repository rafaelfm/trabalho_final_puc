#!/usr/bin/env python

import os, pymongo, json, hashlib, bson
from bson.json_util import dumps as mongo_dumps
from bson.objectid import ObjectId
from bottle import Bottle, request, response, HTTPResponse
from datetime import datetime
from db import get_database_connection

from auth import auth_app, jwt_required, admin_required, authenticate

application = Bottle()
app = application
app.merge(auth_app)

user = None

# atender requisicoes do tipo get para /
@app.get('/')
def index():
    return "Boa sorte!"

# atender requisicoes do tipo post para /api/v1/signin
# curl -H "Content-Type: application/json" -X POST -d '{"email":"scott@gmail.com", "password":"12345"}' http://localhost:8080/api/v1/signin
@app.post('/api/v1/signin')
def login():
    data = request.json
    encoded = authenticate(data['email'], data['password'])
    if encoded:
        return encoded
    else:
        return HTTPResponse(status=401, body="Nao autorizado.")

# atender requisicoes do tipo post para /api/v1/users/create
# curl -i -H "Content-Type: application/json" -X POST -d '{"name": "Eduardo", "email": "xyz@gmail", "password":"xyz"}' http://localhost:8080/api/v1/users/create
@app.post('/api/v1/users/create')
def create_user():	
    response.content_type='application/json'
    data = request.json
    name = data["name"] # obtem nome enviado por parametro postado.
    email = data["email"] # obtem email enviado por parametro postado.
    password = hashlib.md5(data["password"].encode()).hexdigest() # obtem hash md5 da senha enviada.
    db = get_database_connection() # conecta com a base de dados e armazena a conexao em db.
    user = db.users.find_one({'email': email}) # find_one retorna um documento,
                                               # ou None se nao encontrar nenhum.
    if user:
        # usuario ja existe. retornar em formato JSON padrao com mensagem.
        return json.dumps({'success': True, 'msg': 'usuario ja existente.'})
    else:
        # usuario nao existe. inserir novo usuario.
        db.users.insert({'name': name, 'email': email, 'password': password})
        # retornar em formato JSON padrao com mensagem.
        return json.dumps({'success': True, 'msg': 'usuario cadastrado.'})
# atender requisicoes do tipo get para /api/v1/users
# curl -i -H "Content-Type: application/json" -X GET  http://localhost:8080/api/v1/users

#inicio editar usuário
# atender requisicoes do tipo post para /api/v1/users/<user_id>/edit
# {"name":"Diego França","email":"diegofnbh@gmail.com"} http://localhost:8080/api/v1/user/<user_id>/edit
@app.post('/api/v1/user/<user_id>/edit')
@jwt_required
def edit_user(user, user_id):
    response.content_type='application/json'
    data = request.json
    db = get_database_connection()
    try:
        user = db.users.find_one({'_id': ObjectId(user_id)}) #Pesquisa pelo usuário
    except Exception:
        return json.dumps({'success': True, 'msg': 'usuario não ecadastrado.'})

    if user:
        # usuario ja existe. fazer a atualização do nome e e-mail
        db.users.update({"_id": ObjectId(user_id)},{"$set":{"name": data["name"],	"email": data["email"]}})
        return  json.dumps({'success': True, 'msg': 'usuario alterado.'})
    else:
        return json.dumps({'success': True, 'msg': 'usuario não existecadastrado.'})
#Fim user/<user_id>/edit

#inicio editar senha do usuário
# atender requisicoes do tipo post para /api/v1/users/<user_id>/change_password
# {"password":"123"} http://localhost:8080/api/v1/user/57b9ab441f8fed23946bbfc3/change_password
@app.post('/api/v1/user/<user_id>/change_password')
@jwt_required
def change_password(user, user_id):
    response.content_type='application/json'
    data = request.json
    db = get_database_connection()
    try:
        user = db.users.find_one({'_id': ObjectId(user_id)}) # find_one retorna um documento, buscando pelo ID
    except Exception:
        return json.dumps({'success': True, 'msg': 'usuario não ecadastrado favor selecionar um usuário válido.'})

     # Se encontrou o usuário, efetua alteração
    if user:
        password = hashlib.md5(data["password"].encode()).hexdigest()  # obtem hash md5 da senha enviada.
        # usuario ja existe. efetuar alteração da senha
        db.users.update({"_id": ObjectId(user_id)},{"$set":{"password": password}})
        # retornar em formato JSON padrao com mensagem.
        return  json.dumps({'success': True, 'msg': 'usuario alterado.'})
    else:
        # usuario nao existe. inserir novo usuario.
        return json.dumps({'success': True, 'msg': 'usuario não cadastrado.'})
#Fim user/<user_id>/change_password

# atender requisicoes do tipo get para /api/v1/menu/items
# http://localhost:8080/api/v1/menu/items
#fim
@app.get('/api/v1/menu/items')
def list_itens():
    response.content_type='application/json'
    db = get_database_connection() # conecta com a base de dados e armazena a conexao em db.
    itens = db.itens.find()
    return mongo_dumps(itens)
#Fim /menu/itens

# atender requisicoes do tipo post para /api/v1/user/<user_id>/orders/create
# [{"nome":"Macarrão","preco":35.99},{"nome":"Salmão","preco":55.99},{"nome":"Refrigerante","preco":5.99},{"nome":"Pudim","preco":5.99}]http://localhost:8080/api/v1/user/57bb948e1f8fed11483bc05c/orders/create
@app.post('/api/v1/user/<user_id>/orders/create')
@jwt_required
def create_orders(user,user_id):
    response.content_type='application/json'
    data = request.json
    items = data
    totalPedido = 0.0
    db = get_database_connection() # conecta com a base de dados e armazena a conexao em db.
    contador = 0
    for item in items:
        NomeItem =  item["nome"]
        ItemdePedido = db.itens.find_one({'nome': NomeItem}) # find_one retorna um documento, buscando pelo ID
        if ItemdePedido["preco"] > 0:
            items[contador]["preco"] = ItemdePedido["preco"] #Aqui eu quero atualizar a lista
            contador = contador + 1
        totalPedido += ItemdePedido["preco"]
#        totalPedido += item['preco'] #Guarda na variável totalPedido a soma do valor dos itens

    db.orders.insert({
        "data": datetime.now(),
        "total": totalPedido,
        "IdUsuario":ObjectId(user_id),
        "usuario": user,
        "items": items
    })
    # retornar em formato JSON padrao com mensagem.
    return json.dumps({'success': True, 'msg': 'Pedido Cadastrado com Sucesso.'})
#Fim /api/v1/user/<user_id>/orders/create'

# atender requisicoes do tipo get para /api/v1/user/<user_id>/orders
# http://localhost:8080/api/v1/user/57bb948e1f8fed11483bc05c/orders
@app.get('/api/v1/user/<user_id>/orders')
def lista_pedidos_usuario(user_id):
    response.content_type='application/json'
    data = request.json
    db = get_database_connection()
    try:
        usuario = db.users.find_one({'_id': ObjectId(user_id)})
    except Exception:
        return json.dumps({'success': True, 'msg': 'usuario não ecadastrado.'})

    try:
        Pedidos = db.orders.find({'IdUsuario':ObjectId(user_id)}) # retorna os documentos, buscando pelo ID usuário
    except Exception:
        return json.dumps({'success': True, 'msg': 'pedido nao cadastrado.'})

    return mongo_dumps(Pedidos)
#Fim /api/v1/user/<user_id>/orders

# atender requisicoes do tipo get para /api/v1/user/<user_id>/orders/<order_id>
# http://localhost:8080/api/v1/user/57bb948e1f8fed11483bc05c/orders/57bce01c1f8fed1f48c61933
@app.get('/api/v1/user/<user_id>/orders/<order_id>')
def lista_pedidos(user_id, order_id):
    response.content_type='application/json'
    data = request.json
    db = get_database_connection()
    try:
        user = db.users.find_one({'_id': ObjectId(user_id)})
    except Exception:
        return json.dumps({'success': True, 'msg': 'usuario não ecadastrado.'})
    numeropedido = ObjectId(order_id)
    try:
        detalhepedido = db.orders.find_one({'_id':numeropedido}) # find_one retorna um documento, buscando pelo ID do pedido e número do usuário
    except Exception:
        return json.dumps({'success': True, 'msg': 'pedido nao cadastrado.'})

    return mongo_dumps(detalhepedido)
#Fim /api/v1/user/<user_id>/orders/<order_id>

# /api/v1/admin/menu/sessions/create
# {"sessao": "Bebidas"} - http://localhost:8080/api/v1/admin/menu/sessions/create
#fim
@app.post('/api/v1/admin/menu/sessions/create')
def create_sessao_menu():
    response.content_type='application/json'
    data = request.json
    sessao = data["sessao"]
    db = get_database_connection()
    db.sessao.insert({'sessao': sessao})
    return json.dumps({'success': True, 'msg': 'sessão cadastrada com sucesso.'})
#Fim /api/v1/admin/menu/sessions/create'

# atender requisicoes do tipo post para /api/v1/admin/menu/items/create'
# {"nome": "Ervas", "preco": 25.99, "sessao":"Entrada"} http://localhost:8080/api/v1/admin/menu/items/create
@app.post('/api/v1/admin/menu/items/create')
def create_itens_menu():
    response.content_type='application/json'
    data = request.json
    nome = data["nome"]
    preco = data["preco"]
    sessao = data["sessao"]
    db = get_database_connection()
    db.itens.insert({'nome': nome, 'preco': preco, 'sessao': sessao})
    return json.dumps({'success': True, 'msg': 'item cadastrado.'})
#fim /menu/items/create

@app.get('/api/v1/users')
@jwt_required
def list_user(user):
    response.content_type='application/json'
    db = get_database_connection() # conecta com a base de dados e armazena a conexao em db.
    users = db.users.find()
    return mongo_dumps(users)
# atender requisicoes do tipo get para /api/v1/admin/users
# curl -i -H "Content-Type: application/json" -X GET  http://localhost:8080/api/v1/admin/users

@app.get('/api/v1/admin/users')
@admin_required
def list_user_from_admin(user):
    response.content_type='application/json'
    db = get_database_connection() # conecta com a base de dados e armazena a conexao em db.
    users = db.users.find()
    return mongo_dumps(users)

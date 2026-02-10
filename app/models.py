from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.extensions import db
import enum



class User(db.Model):
	__tablename__ = "user"

	id = db.Column(db.Integer, primary_key=True) 
	nome = db.Column(db.String(30), nullable = False) 
	email = db.Column(db.String(50), unique = True, nullable = False) 
	password = db.Column(db.String(50), nullable = False)
	isAdmin = db.Column(db.Boolean, default = False)

class Reserva(db.Model):
	__tablename__ = "reserva"

	id = db.Column(db.Integer, primary_key=True)
	idUser = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
	idEspaco = db.Column(db.Integer, db.ForeignKey('espaco.id'), nullable = False)
	dataInicio = db.Column(db.DateTime, nullable=False)
	dataFim = db.Column(db.DateTime, nullable=False)
	estado = db.Column(db.String(20), default ="ativa")

	
		 
class Espaco(db.Model):
	__tablename__ = "espaco"

	id = db.Column(db.Integer, primary_key=True)
	nome = db.Column(db.String(30), nullable = False)
	descricao = db.Column(db.Text)
	imagem = db.Column(db.String(200))
	precoHora = db.Column(db.Float, nullable = False)
	ativo = db.Column(db.Boolean, nullable = False)


class Pagamento(db.Model):
	__tablename__ = "pagamento"

	id = db.Column(db.Integer, primary_key=True)
	idUser = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
	idReserva = db.Column(db.Integer, db.ForeignKey('reserva.id'), nullable = False)
	valor = db.Column(db.Float, nullable = False)
	dataPagamento = db.Column(db.DateTime)
	estado = db.Column(db.String(20), default="pendente")
	
	

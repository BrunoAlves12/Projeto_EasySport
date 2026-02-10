from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import enum

db = SQLAlchemy(app)

class EstadoReserva(enum.Enum):
	ativa = "Ativa"
	cancelada = "Cancelada"
	concluida = "Concluida"


class User():
	id = db.Column(db.Integer, primary_key=True) 
	nome = db.Column(db.String(30), nullable = False) 
	email = db.Column(db.String(50), nullable = False) 
	password = db.Column(db.String(50), nullable = False)
	isAdmin = db.Column(db.Bool, nullable = False)

class Reserva():
	id = db.Column(db.Integer, primary_key=True)
	idUser = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
	idEspaco = db.Column(db.Integer, db.ForeignKey('espaco.id'), nullable = False)
	dataInicio = db.Column(db.Integer, db.Date, nullable = False)
	dataFim = db.Column(db.Integer, db.Date, nullable = False)
	estado = db.Column(db.Enum(EstadoReserva), nullable= False, default=EstadoReserva.ativa)

	
		 
class Espaco():
	id = db.Column(db.Integer, primary_key=True)
	nome = db.Column(db.String(30), nullable = False)
	descricao = db.Column(db.String(100), nullable = False)
	imagem = db.Column(db.String(30), nullable = False)
	precoHora = db.Column(db.Decimal, nullable = False)
	ativo = db.Column(db.Bool, nullable = False)

class Pagamento():
	id = db.Column(db.Integer, primary_key=True)
	idUser = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
	idReserva = db.Column(db.Integer, db.ForeignKey('reserva.id'), nullable = False)
	valor = db.Column(db.Decimal, nullable = False)
	dataPagamento = db.Column(db.Integer, db.Date, nullable = False)
	estado = db.Column(db.Bool, nullable = False)
	
	

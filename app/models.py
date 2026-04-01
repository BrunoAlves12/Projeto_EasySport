import enum

from app.extensions import db

class EstadoUser(enum.Enum):
    ativo = "ativo"
    inativo = "inativo"

class EstadoReserva(enum.Enum):
	pendente = "pendente"
	confirmada = "confirmada"
	cancelada = "cancelada"
    

class User(db.Model):
	__tablename__ = "user"

	id = db.Column(db.Integer, primary_key=True) 
	nome = db.Column(db.String(30), nullable = False) 
	username = db.Column(db.String(30), unique=True, nullable=False)
	email = db.Column(db.String(50), unique = True, nullable = False) 
	password = db.Column(db.String(50), nullable = False)
	dataNascimento = db.Column(db.Date)
	isAdmin = db.Column(db.Boolean, default = False)
	estado = db.Column(db.Enum(EstadoUser), default=EstadoUser.ativo)
	reservas = db.relationship("Reserva", back_populates="user", lazy=True)
	pagamentos = db.relationship("Pagamento", back_populates="user", lazy=True)

class Reserva(db.Model):
	__tablename__ = "reserva"

	id = db.Column(db.Integer, primary_key=True)
	idUser = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
	idEspaco = db.Column(db.Integer, db.ForeignKey('espaco.id'), nullable = False)
	dataInicio = db.Column(db.DateTime, nullable=False)
	dataFim = db.Column(db.DateTime, nullable=False)
	estado = db.Column(db.Enum(EstadoReserva), default=EstadoReserva.pendente)
	user = db.relationship("User", back_populates="reservas")
	espaco = db.relationship("Espaco", back_populates="reservas")
	pagamento = db.relationship("Pagamento", back_populates="reserva", uselist=False)

	
		 
class Espaco(db.Model):
	__tablename__ = "espaco"

	id = db.Column(db.Integer, primary_key=True)
	nome = db.Column(db.String(30), nullable = False)
	modalidade = db.Column(db.String(40))
	descricao = db.Column(db.Text)
	imagem = db.Column(db.String(200))
	precoHora = db.Column(db.Float, nullable = False)
	ativo = db.Column(db.Boolean, nullable = False)
	reservas = db.relationship("Reserva", back_populates="espaco", lazy=True)


class Pagamento(db.Model):
	__tablename__ = "pagamento"

	id = db.Column(db.Integer, primary_key=True)
	idUser = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
	idReserva = db.Column(db.Integer, db.ForeignKey('reserva.id'), nullable = False, unique=True)
	nomeFaturacao = db.Column(db.String(80))
	emailFaturacao = db.Column(db.String(120))
	morada = db.Column(db.String(160))
	codigoPostal = db.Column(db.String(20))
	localidade = db.Column(db.String(80))
	pais = db.Column(db.String(80))
	ultimos4Cartao = db.Column(db.String(4))
	valor = db.Column(db.Float, nullable = False)
	dataPagamento = db.Column(db.DateTime)
	estado = db.Column(db.String(20), default="pendente")
	user = db.relationship("User", back_populates="pagamentos")
	reserva = db.relationship("Reserva", back_populates="pagamento")
	

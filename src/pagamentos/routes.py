from flask import Blueprint, request, jsonify
#from .service import create_user

rotas_pagamento = Blueprint("pagamento", __name__, url_prefix="/pagamento")

@rotas_pagamento.route("processar_pagamento", methods=["POST"])
def processar_pagamento():
	pass

@rotas_pagamento.route("ver_pagamento", methods=["GET"])
def ver_pagamento():
	pass

@rotas_pagamento.route("ver_pagamentos", methods=["GET"])
def ver_pagamentos():
	pass

@rotas_pagamento.route("cancelar_pagamento", methods=["DELETE"])
def cancelar_pagamento():
	pass


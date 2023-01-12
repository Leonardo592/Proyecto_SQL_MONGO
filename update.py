
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Comparison

# Ejemplos
stringa1 = 'UPDATE people SET status = "C" WHERE age > 25'
stringa2 = 'UPDATE people SET age = age + 3 WHERE status = "A"'
stringa3 = 'UPDATE people SET status = "C", name = "Carlo" WHERE age > 25' 
stringa4 = 'UPDATE people SET status = "C", age = age + 1, name = "Carlo"  WHERE age > 25'


def update(tokens):
  tabla = ""
  encontrar_where = False
  encontrar_set = False
  set_salida = ""
  is_inc = False
  conj_salida_interior = []
  establecer_parentesis_salida = ""
  encontrar_listaId = False
# scorre tutti i token per individuare il nome della tabella e trovare la condizione del where,
# che viene memorizzata nel vettore parsed.
# (es) parsed -> ['status', '=', '"D"', 'OR', 'name', '<=', '"Carlo"', 'AND', 'name', '!=', '"Saretta"']
  for token in tokens:
    if isinstance(token, Identifier):
      tabla = token.value
    if token.value == "SET":
      encontrar_set = True
    if isinstance(token,IdentifierList):
      encontrar_listaId = True
      conj_salida_interior = convertir_multiples_condiciones_update(token)
    if isinstance(token,Comparison) and encontrar_set:
      encontrar_set = False
      establecer_parentesis_salida = convertir_una_sola_condicion_update(token)
    if isinstance(token, Where):
      encontrar_where = True
      salida = convertir_condicion_where(token)
  # Se devono essere aggiornate più campi, allora costruisce la query di output in modo opportuno
  if encontrar_listaId:
    establecer_parentesis_salida = formato_salida_listaId(conj_salida_interior)
   

  # Se nella condizione del where erano presenti degli operatori logici 
  # allora utilizzali per la costruzione della query finale, altrimenti
  # se era una condizione semplice costruisci la query finale con solamente
  # l'unico selettore presente.
  if isinstance(salida[0],LogicOperator):
    consulta_final = "db."+ tabla +".update(" + salida[-1].created_string + ", " + establecer_parentesis_salida + " )"
  else:
    parentesis_salida = convertir_condicion_a_mongo(salida) 
    consulta_final = "db." + tabla + ".update(" + str(parentesis_salida[0]) + ", " + establecer_parentesis_salida +  ")"
  return(consulta_final)


def formato_salida_listaId(conj_salida_interior):
  establecer_parentesis_salida = ""
  combinar= combinar_subconjunto_lista(conj_salida_interior)
  contador = 0
  for tipo, value in combinar.items():
    contador = contador + 1
    establecer_parentesis_salida = establecer_parentesis_salida + "{" + tipo + ": "
    for i, val in enumerate(value):
      establecer_parentesis_salida = establecer_parentesis_salida  +"{"+ val + "}"
      if i != len(value)-1:
        establecer_parentesis_salida = establecer_parentesis_salida + ", "
      else:
        establecer_parentesis_salida = establecer_parentesis_salida + "}"
    if contador != len(combinar.items()):
      establecer_parentesis_salida = establecer_parentesis_salida + ", "
  return establecer_parentesis_salida

def convertir_multiples_condiciones_update(token):
  salida = []
  for id in token:
    if isinstance(id,Comparison):
      salida.append(crear_conjunto_salida_para_listaId(id))
  return salida

def convertir_una_sola_condicion_update(token):
  is_inc = False
  set_salida = token.value.split(" ")
  if (set_salida[0] == set_salida[2]):
    establecer_operador = "$inc"
    is_inc = True
  else:
    establecer_operador = "$set"
  if is_inc:
    segundo_elemento = set_salida[4]
  else:
    segundo_elemento = set_salida[2]
  establecer_parentesis_salida = "{" + establecer_operador + ": {" + set_salida[0] + ": " + segundo_elemento + "}}"
  return establecer_parentesis_salida
"""
def merge_subset_list_old(list):
  list1 = list.copy()
  list2 = list.copy()
  combinar = []
  for subset1 in list1:
    is_merged = False
    for subset2 in list2:
      if subset1.tipo == subset2.tipo and subset1.value != subset2.value:
        ss = SubSet(subset1.tipo, str(subset1.value + ", " + subset2.value))
        list1.remove(subset1)
        list2.remove(subset2)
        combinar.append(ss)
        is_merged = True
    if not is_merged:
      combinar.append(subset1)
      list1.remove(subset1)
  return combinar
"""
def combinar_subconjunto_lista(list):
  diccionario = {}
  for item in list:
    if item.tipo not in diccionario:
      diccionario[item.tipo] = [item.value]
    else:
      diccionario[item.tipo].append(item.value)
  return diccionario

def crear_conjunto_salida_para_listaId(token):
  is_inc = False
  salida = ""
  set_salida = token.value.split(" ")
  if (set_salida[0] == set_salida[2]):
    establecer_operador = "$inc"
    is_inc = True
  else:
    establecer_operador = "$set"
  if is_inc:
    segundo_elemento = set_salida[4]
  else:
    segundo_elemento = set_salida[2]
  if (set_salida[0] == set_salida[2]):
    establecer_operador = "$inc"
    is_inc = True
  else:
    establecer_operador = "$set"
  if is_inc:
    segundo_elemento = set_salida[4]
  else:
    segundo_elemento = set_salida[2]
  #output = "{ " + establecer_operador + ": {" + set_salida[0] + ": " + segundo_elemento + "}}"
  salida = SubSet(establecer_operador, str(set_salida[0] + ": " + segundo_elemento))
  return salida

class SubSet:#SUBCONJUNTO
  def __init__(self, tipo = None, value = None):
    self.tipo = tipo
    self.value = value
  def __str__(self):
      return (str(self.__class__) + ": " + str(self.__dict__))

# Una volta trovata la condizione del where, scorre tutti i suoi token 
# per memorizzare nel dizionario posiciones_operador_logico il tipo di operatore logico 
# e la sua posizione all'interno della condizione where.
# (es) posiciones_operador_logico -> {3: 'OR', 7: 'AND'}

def crear_posicion_operador(parsed):
  posiciones_operador_logico = {}
  for i, item in enumerate(parsed, start = 0):
    if item == "AND" or item == "OR":
      posiciones_operador_logico[i] = "{0}".format(item)
  return posiciones_operador_logico

# Crea il vettore 2D lista_where_2D, che contiene al suo interno tante liste
# di token quante sono le sottocondizioni di cui è composto il where.
# (es) lista_where_2D -> [['status', '=', '"D"'], ['name', '<=', '"Carlo"'], ['name', '!=', '"Saretta"']]

def crear_lista_subcondiciones(posiciones_operador_logico, parsed):
  posicion_inicial = 0
  lista_where_2D = []
  for key, value in posiciones_operador_logico.items():
    lista_temp = parsed[posicion_inicial:key]
    lista_where_2D.append(lista_temp)
    posicion_inicial = key + 1
    # Nel momento in cui viene raggiunto l'ultimo operatore logico, 
    # deve essere costruita l'ultima sottolista di lista_where_2D prendendo 
    # tutti i token rimamente in parsed.
    if key == list(posiciones_operador_logico.items())[-1][0]: 
      lista_temp = parsed[posicion_inicial:len(parsed)]
      lista_where_2D.append(lista_temp)
  return lista_where_2D

# A questo punto avviene la traduzione delle sottocondizione da sql a sintassi mongodb,
# inanzitutto traducendo il selettore (che è sempre l'elemento centrale di ogni sottolista)
# e poi memorizzando il risultato finale nel vettore output_parenthesis.
# (es) output_parenthesis -> ['{ status: { $eq: "D" }}', '{ name: { $lte: "Carlo" }}', '{ name: { $ne: "Saretta" }}']
def convertir_subcondiciones_a_mongo(lista_where_2D):
  parentesis_salida = []
  for item in lista_where_2D:
    if item[1] == "=":
      selector = "$eq"
    elif item[1] == "!=":
      selector = "$ne"
    elif item[1] == ">":
      selector = "$gt"
    elif item[1] == ">=":
      selector = "$gte"
    elif item[1] == "<":
      selector = "$lt"
    elif item[1] == "<=":
      selector = "$lte"
    sub_salida = "{ "+ item[0] +": { "+selector+": " + item[2] + "}"
    parentesis_salida.append(sub_salida + "}")
  return parentesis_salida

# Viene creato il vettore prioridad_operador_logico assegnando ad ogni operatore logico
# una differente priorità: dovranno infatti essere prima eseguiti tutti gli AND
# da sinistra a destra, e poi tutti gli OR da sinistra a destra.
# (es) prioridad_operador_logico -> [7, 3]
def crear_prioridad_operadores(posiciones_operador_logico):
  prioridad_operador_logico = []
  operadores_logicos = []
  for key, value in posiciones_operador_logico.items():
    if value == "AND":
      prioridad_operador_logico.append(key)
  for key, value in posiciones_operador_logico.items():
    if value == "OR":
      prioridad_operador_logico.append(key)

  # Vengono ora unite le posizioni, le priorità e i valori (AND/OR) 
  # di tutti gli operatori logici negli oggetti LogicOperator,
  # i quali vengono aggiunti alla lista operadores_logicos.
  # (es) operadores_logicos[0] -> {'pos': 3, 'tipo': 'OR', 'prioridad': 1, 'left': None, 'right': None, 'created_string': None}
  for key, value in posiciones_operador_logico.items():
    op = LogicOperator()
    op.pos = key
    op.tipo = value
    op.prioridad = prioridad_operador_logico.index(key)
    operadores_logicos.append(op)
  return operadores_logicos

# Per ogni sottolista contenuta in lista_where_2D viene creato un oggetto Block,
# e aggiunto alla lista blocks. Ogni blocco avrà come attributi l'id/posizione del blocco,
# il valore in sql (estratto da lista_where_2D)
# ed il valore in mongodb (estratto da output_parenthesis).
# (es) blocks[0] -> {'id': 0, 'valor_sql': ['status', '=', '"D"'], 'valor_mongo': '{ status: { $eq: "D" }}', 'mapeo': None}

def crear_blocks(lista_where_2D, parentesis_salida):
  blocks = []
  for i, item in enumerate(lista_where_2D, start = 0):
    block = Block(i, item, parentesis_salida[i])
    blocks.append(block) 
  return blocks

# Ogni operatore logico in operadores_logicos viene mappato con la sottocondizione di sinistra (op.left)
# e con la sottocondizione di destra (op.right) in base alla sua posizione
# relativa nella condizione where.
# Le sottocondizioni possono essere dei blocchi (nel caso degli operatori con priorità
# di esecuzione maggiore) oppure il risultato di altri operatori eseguiti precedentemente.
# (es) operadores_logicos[0] -> {'pos': 7, 'tipo': 'AND', 'prioridad': 0, 'left': <__main__.Block object at 0x7f12d8b5ee80>, 'right': <__main__.Block object at 0x7f12d8b5ee48>, 'created_string': None}
def mapear(operadores_logicos, blocks):
  for op in operadores_logicos:
    pos_block_rel = op.posicion//3
    id_block_izq = pos_block_rel - 1
    id_block_der = pos_block_rel
    for block in blocks:
      if block.id == id_block_izq and block.mapeo == None:
        block.mapeo = op
        op.izquierda = block
      elif block.id == id_block_izq and block.mapeo != None:
        op.izquierda = block.mapeo
      elif block.id == id_block_der and block.mapeo == None:
        block.mapeo = op
        op.derecha = block
      elif block.id == id_block_der and block.mapeo != None:
        op.derecha = block.mapeo

# Viene eseguita la traduzione in mongoDB degli operatori, 
# partendo da quelli con priorità maggiore e memorizzando il risultato
# parziale nell'attributo created_string del blocco. Gli operatori successivi
# che hanno come mapear left o right quel blocco appena eseguito costruiranno
# in modo incrementale il risultato a partire dal valore di created_string.
# Il risultato finale della traduzione sarà quindi contenuto nell'attributo
# created_string dell'ultimo blocco.
def ejecutar_operadores (operadores_logicos):
  ult_id_op_ejec = None
  for op in operadores_logicos:
    if isinstance(op.izquierda, Block) and isinstance(op.derecha, Block):
      valor_izquierdo = op.izquierda.valor_mongo
      valor_derecho = op.derecha.valor_mongo
      ult_id_op_ejec = op.posicion
    elif isinstance(op.izquierda, OperadorLogico) and isinstance(op.derecha, Block):
      valor_izquierdo = buscar(operadores_logicos,ult_id_op_ejec).cadena_creada
      valor_derecho = op.derecha.valor_mongo
      ult_id_op_ejec = op.posicion
    elif isinstance(op.izquierda, Block) and isinstance(op.derecha, OperadorLogico):
      valor_izquierdo = op.izquierda.valor_mongo
      valor_derecho = buscar(operadores_logicos,ult_id_op_ejec).cadena_creada
      ult_id_op_ejec = op.posicion
    elif isinstance(op.izquierda, OperadorLogico) and isinstance(op.derecha, OperadorLogico):
      valor_izquierdo = buscar(operadores_logicos,ult_id_op_ejec).cadena_creada
      valor_derecho = buscar(operadores_logicos,ult_id_op_ejec).cadena_creada
      ult_id_op_ejec = op.posicion
    op.cadena_creada  = "{$" + op.tipo.lower() + ": [" + str(valor_izquierdo) + ", " +  str(valor_derecho) + "]}"

def convertir_condicion_a_mongo(parsed):
  parentesis_salida = []
  selector = ""
  for item in parsed:
    if item == "=":
      selector = "$eq"
    elif item == "!=":
      selector = "$ne"
    elif item == ">":
      selector = "$gt"
    elif item == ">=":
      selector = "$gte"
    elif item == "<":
      selector = "$lt"
    elif item == "<=":
      selector = "$lte"
  sub_salida = "{"+ parsed[0] +": {"+selector+": " + parsed[2] + " }"
  parentesis_salida.append(sub_salida + "}")
  return parentesis_salida

def convertir_condicion_where(token):
  parsed = token.value.split(" ")
  where = "WHERE"
  if where in parsed: parsed.remove(where)
  #parsed.remove("WHERE")
  posiciones_operador_logico = crear_posicion_operador(parsed)
  if posiciones_operador_logico:
    lista_where_2D = crear_lista_subcondiciones(posiciones_operador_logico, parsed)
    parentesis_salida = convertir_subcondiciones_a_mongo(lista_where_2D)
    operadores_logicos = crear_prioridad_operadores(posiciones_operador_logico)
    blocks = crear_blocks(lista_where_2D, parentesis_salida)
   # Gli operatori logici vengono ordinati in base alla loro priorità di esecuzione.
    operadores_logicos.sort(key=lambda x: x.prioridad, reverse=False)
    mapear(operadores_logicos,blocks)
    execute_ops(operadores_logicos)
    salida = operadores_logicos
  else:
    salida = parsed
  return salida

# Classe dell'operatore logico AND/OR. La pos indica la posizione all'interno della condizione where,
# (e quindi funge da id), il tipo indica il tipo AND/OR, la priorità l'ordine di esecuzione, left e right
# le sottocondizione di sinistra e di destra, mentre su created_string viene memorizzato il risultato 
# della sua traduzione in sintassi mongoDB.
class LogicOperator:
    def __init__(self, pos = None, tipo = None, prioridad = None, left = None, right = None, created_string = None):
      self.pos = pos
      self.tipo = tipo
      self.prioridad = prioridad
      self.left = left
      self.right = right
      self.created_string = created_string
    def __str__(self):
      return (str(self.__class__) + ": " + str(self.__dict__))


# La classe blocco indica una sottocondizione che precede o segue un operatore logico 
# nella condizione del where iniziale. Esso è quindi caratterizzato da un id (posizione del blocco), 
# da una traduzione in sql (valor_sql) ed uno in mognodb (valor_mongo).
# L'attributo mapeo serve per mappare un operatore successivo con uno precedente 
# che ha già mappato quel blocco.
class Block:
  def __init__(self, id, valor_sql = None, valor_mongo = None, mapeo = None):
    self.id = id
    self.valor_sql = valor_sql
    self.valor_mongo = valor_mongo
    self.mapeo = mapeo
  def __str__(self):
    return (str(self.__class__) + ": " + str(self.__dict__))

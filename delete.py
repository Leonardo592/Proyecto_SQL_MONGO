import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where

# EJEMPLOS
stringa1 = 'DELETE FROM molise;'
stringa2 = 'DELETE FROM people WHERE status = "D"'
stringa3 = 'DELETE FROM people WHERE status = "D" and name <= "Carlo" or name != "Saretta"'
stringa4 = 'DELETE FROM people WHERE status = "D" or name <= "Carlo" and name != "Saretta"'
stringa5 = 'DELETE FROM people WHERE status = "D" and name <= "Carlo" and name != "Saretta"'
stringa6 = 'DELETE FROM people WHERE status = "D" or name <= "Carlo" and name != "Saretta" or age >= 18'


# DELETE WHERE - elimina tuplas de la tabla con una determinada condición
def delete(tokens):
  tabla = ""
  encontrar_where = False
# iterar a través de todos los tokens para ubicar el nombre de la tabla y encontrar la condición where,
# que se almacena en el vector analizado.
# (es) parsed -> ['status', '=', '"D"', 'OR', 'name', '<=', '"Carlo"', 'AND', 'name', '!=', '"Saretta"']
  for token in tokens:
    if isinstance(token, Identifier):
      tabla = token.value #nombre de la tabla
    if isinstance(token, Where):
      encontrar_where = True
      salida = convertir_condicion_where(token)
      # Si los operadores lógicos estuvieran presentes en la condición where 
      # luego utilícelos para la construcción de la consulta final, de lo contrario
      # si fuera una condición simple, cree la consulta final con solo
      # el único selector presente.
      if isinstance(salida[0],OperadorLogico):
        consulta_final = "db."+ tabla +".deleteMany(" + salida[-1].cadena_creada + ")"
      else:
        parentesis_salida = convertir_condicion_a_mongo(salida) 
        consulta_final = "db." + tabla + ".deleteMany(" + str(parentesis_salida[0]) + ")"
  if not encontrar_where:
    consulta_final = "db."+str(tabla)+".deleteMany({})"
  return(consulta_final)




# Una vez que se encuentra la condición where, iterar a través de todos sus tokens
# para almacenar el tipo de operador lógico en el diccionario posiciones_operador_logico
# y su posición dentro de la condición where.
# (ej.) posiciones_operador_logico -> {3: 'O', 7: 'Y'}

def crear_posicion_operador(parsed):
  posiciones_operador_logico = {}
  for i, item in enumerate(parsed, start = 0):
    if item == "AND" or item == "OR":
      posiciones_operador_logico[i] = "{0}".format(item)
  return posiciones_operador_logico


# Cree el vector 2D lista_where_2D, que contiene muchas listas dentro
# de tokens de cuántas subcondiciones está compuesto el dónde.
# (es) lista_where_2D -> [['status', '=', '"D"'], ['name', '<=', '"Carlo"'], ['name', '!=', '"Saretta"']]

def crear_lista_subcondiciones(posiciones_operador_logico, parsed):
  posicion_inicial = 0
  lista_where_2D = []
  for key, value in posiciones_operador_logico.items():
    lista_temp = parsed[posicion_inicial:key]
    lista_where_2D.append(lista_temp)
    posicion_inicial = key + 1
    # Cuando se alcanza el último operador lógico,
    # la última sublista de lista_where_2D debe construirse tomando
    # todos los tokens restantes analizados.
    if key == list(posiciones_operador_logico.items())[-1][0]: 
      lista_temp = parsed[posicion_inicial:len(parsed)]
      lista_where_2D.append(lista_temp)
  return lista_where_2D


# En este punto, las subcondiciones se traducen de sql a sintaxis mongodb,
# primero traduciendo el selector (que siempre es el elemento central de cualquier sublista)
# y luego almacenar el resultado final en el vector parentesis_salida.
# (es) parentesis_salida -> ['{ status: { $eq: "D" }}', '{ name: { $lte: "Carlo" }}', '{ name: { $ne: "Saretta" }}']
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
    sub_salida = "{ "+ item[0] +": { "+selector+": " + item[2] + " }"
    parentesis_salida.append(sub_salida + "}")
  return parentesis_salida#valor en mongodb


# El vector prioridad_operador_logico se crea asignando a cada operador lógico
# una prioridad diferente: de hecho, todos los AND deben realizarse primero
# de izquierda a derecha y luego todos los OR de izquierda a derecha.
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


  # Las posiciones, prioridades y valores ahora están fusionados (Y/O)
  # de todos los operadores lógicos en objetos OperadorLogico,
  # que se agregan a la lista operadores_logicos.
  # (es) operadores_logicos[0] -> {'posicion': 3, 'tipo': 'OR', 'prioridad': 1, 'izquierda': None, 'derecha': None, 'cadena_creada': None}
  for key, value in posiciones_operador_logico.items():
    op = OperadorLogico()
    op.posicion = key
    op.tipo = value
    op.prioridad = prioridad_operador_logico.index(key)
    operadores_logicos.append(op)
  return operadores_logicos

# Para cada sublista contenida en lista_where_2D se crea un objeto Block,
# y agregado a la lista de bloques. Cada bloque tendrá como atributos el id/ubicación del bloque,
# el valor en sql (extraído de lista_where_2D)
# y el valor en mongodb (extraído de parentesis_salida).
# (es) blocks[0] -> {'id': 0, 'valor_sql': ['status', '=', '"D"'], 'valor_mongo': '{ status: { $eq: "D" }}', 'mapeo': None}

def crear_blocks(lista_where_2D, parentesis_salida):
  blocks = []
  for i, item in enumerate(lista_where_2D, start = 0):
    block = Block(i, item, parentesis_salida[i])
    blocks.append(block) 
  return blocks


# Cada operador lógico en operadores_logicos se asigna a la subcondición izquierda (op.izquierda)
# y con la subcondición derecha (op.derecha) según su posición
# relativo en la condición where.
# Las subcondiciones pueden ser bloques (en el caso de operadores con prioridad
# de mayor ejecución) o el resultado de otros operadores ejecutados previamente.
# (es) operadores_logicos[0] -> {'posicion': 7, 'tipo': 'AND', 'prioridad': 0, 'izquierda': <__main__.Block object at 0x7f12d8b5ee80>, 'derecha': <__main__.Block object at 0x7f12d8b5ee48>, 'cadena_creada': None}
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

# Los operadores se traducen a mongoDB,
# comenzando desde aquellos con mayor prioridad y almacenando el resultado
# parcial en el atributo cadena_creada del bloque. Operadores posteriores
# ese mapa a la izquierda o a la derecha de ese bloque recién ejecutado se construirá
# incrementalmente el resultado a partir del valor de cadena_creada.
# El resultado final de la traducción estará contenido en el atributo
# cadena_creada del último bloque.
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
  sub_salida = "{ "+ parsed[0] +": { "+selector+": " + parsed[2] + " }"
  parentesis_salida.append(sub_salida + "}")
  return parentesis_salida

def convertir_condicion_where(token):
  parsed = token.value.split(" ")
  parsed.remove("WHERE")
  posiciones_operador_logico = crear_posicion_operador(parsed)
  if posiciones_operador_logico:
    lista_where_2D = crear_lista_subcondiciones(posiciones_operador_logico, parsed)
    parentesis_salida = convertir_subcondiciones_a_mongo(lista_where_2D)
    operadores_logicos = crear_prioridad_operadores(posiciones_operador_logico)
    blocks = crear_blocks(lista_where_2D, parentesis_salida)
    # Los operadores lógicos se ordenan por su prioridad de ejecución.
    operadores_logicos.sort(key=lambda x: x.prioridad, reverse=False)
    mapear(operadores_logicos,blocks)
    ejecutar_operadores(operadores_logicos)
    salida = operadores_logicos
  else:
    salida = parsed
  return salida


# Clase del operador lógico AND/OR. La posicion indica la posición dentro de la condición where,
# (y por lo tanto actúa como un id), el tipo indica el tipo AND/OR, la prioridad, el orden de ejecución, izquierda y derecha
# las subcondiciones izquierda y derecha, mientras que el resultado se almacena en cadena_creada
# de su traducción a la sintaxis mongoDB.
class OperadorLogico:
    def __init__(self, posicion = None, tipo = None, prioridad = None, izquierda = None, derecha = None, cadena_creada = None):
      self.posicion = posicion
      self.tipo = tipo
      self.prioridad = prioridad
      self.izquierda = izquierda
      self.derecha = derecha
      self.cadena_creada = cadena_creada
    def __str__(self):
      return (str(self.__class__) + ": " + str(self.__dict__))



# La clase de bloque indica una subcondición que precede o sigue a un operador lógico
# en la condición inicial donde. Por lo tanto, se caracteriza por una identificación (ubicación del bloque),
# da una traducción en sql (valor_sql) y otra en mognodb (valor_mongo).
# El atributo mapeo se usa para mapear un operador posterior a uno anterior
# que ya ha mapeado ese bloque.
class Block:
  def __init__(self, id, valor_sql = None, valor_mongo = None, mapeo = None):
    self.id = id
    self.valor_sql = valor_sql
    self.valor_mongo = valor_mongo
    self.mapeo = mapeo
  def __str__(self):
    return (str(self.__class__) + ": " + str(self.__dict__))


# Función para encontrar un operador lógico en operadores_logicos por su id/pos
def buscar(list, id):
  resultado = None
  for item in list:
    if item.posicion == id:
      resultado = item
  return resultado
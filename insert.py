import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Function, Parenthesis, Values
import string

# EJEMPLOS
stringa1 = "INSERT INTO items (name,price) VALUES('Kellogs',2);"



def insert(tokens):
  tabla = ""
  #where_found = False
  columnas = []
  valores_temp = []
  valores = []

# iterar a través de tokens para ubicar el nombre de la tabla y encontrar nombres de columnas y nombres de valores,
# que se almacenan en las listas de columnas y valores respectivamente.
# (es) columns -> ['name', 'start_date', 'end_date']
#       values -> ['AI for Marketing', '2019-08-01', '2019-12-31', 'ML for Sales', '2019-05-15', '2019-11-20']
  for token in tokens:
    if isinstance(token, Function):
      tabla = token[0].value
      columnas = encontrar_nombre_columna(token)
    if isinstance(token,Values):
      valores_temp = encontrar_valor_columna(token)

# Formatear elementos de valores para eliminar puntuación y elementos vacíos
  valores = valores_de_formato(valores_temp)

# calcular el nombre de la columna asociada para cada valor y crear la consulta mongodb correspondiente
  parentesis_salida = convertir_a_mongo(columnas, valores)
  

# Si se agrega más de una tupla, el resultado se encierra entre corchetes
  if (len(columnas) != len(valores)):
    parentesis_salida = "[" + parentesis_salida + "]"
  salida = "db." + tabla + ".insert( " + parentesis_salida + " )"
  return salida


def encontrar_nombre_columna(token):
  columnas = []
  for par in token:
    if isinstance(par,Parenthesis):
      for lista_id in par:
        if isinstance(lista_id,IdentifierList):
          for id in lista_id:
            if isinstance(id,Identifier):
              columnas.append(id.value)
  return columnas

def encontrar_valor_columna(token):
  valores_temp = []
  for par in token:
    if isinstance(par,Parenthesis):
      for lista_id in par:
        if isinstance(lista_id,IdentifierList):
          for id in lista_id:
            valores_temp.append(id.value)
  return valores_temp

def valores_de_formato(valores_temp):
  valores = []
  new_s_p = string.punctuation.translate(str.maketrans('','','-'))
  for s in valores_temp:
      s = s.translate(str.maketrans('','',new_s_p))
      valores.append(s)
  valores = list(filter(None, valores))
  return valores

def convertir_a_mongo(columnas, valores):
  parentesis_salida = ""
  for i, value in enumerate(valores, start = 0):
    primer_elemento = ""
    ultimo_elemento = ""
    id_col = i%len(columnas)
    if id_col == 0:
      primer_elemento = "{"
    elif id_col == len(columnas)-1:
      ultimo_elemento = "}"
    parentesis_salida = parentesis_salida + primer_elemento +columnas[id_col]  + ": '" + value + "'" + ultimo_elemento
    if value != valores[-1]:
      parentesis_salida = parentesis_salida + ", "
  return parentesis_salida
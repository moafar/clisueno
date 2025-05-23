from pathlib import Path
import os
import logging
from utils.texto_utils import extraer_texto_docx, extraer_texto_rtf, extraer_texto_doc, normalizar_texto, extraer_subcadenas, determinar_tipos_examenes
from utils.procesar_psg import procesar_psg_doc, procesar_psg_rtf
from utils.procesar_cpap import procesar_cpap_doc, procesar_cpap_rtf, procesar_cpap_docx
from utils.procesar_dam import procesar_dam_doc, procesar_dam_rtf
from utils.procesar_bpap import procesar_bpap_doc, procesar_bpap_rtf
from utils.procesar_actigrafia import procesar_actigrafia_doc
from utils.procesar_capnografia import procesar_capnografia_doc, procesar_capnografia_rtf
from utils.procesar_autocpap import procesar_autocpap_docx
from utils.procesar_poligrafia import procesar_poligrafia_docx
import csv

def procesar_archivo(archivo: Path) -> None:
    """Lee el contenido de un archivo y retorna el texto extraído o None si hay un error."""
    
    _, extension = os.path.splitext(archivo)
    texto = ""

    try:
        extension = extension.lower()

        if extension == ".docx":
            texto = extraer_texto_docx(archivo)
        elif extension == ".rtf":
            texto = extraer_texto_rtf(archivo)
        elif extension == ".doc":
            texto = extraer_texto_doc(archivo)
        else:
            logging.error(f"Extensión de archivo no soportada: {extension}")
            return None        
        
    except Exception as e:
        logging.error(f"Error inesperado al leer {archivo} $$ {e}")
        return None

    #print(texto)  # Para verificar el texto extraído
    #logging.debug(f"Texto extraído: {texto}")

    texto_normalizado = normalizar_texto(texto)  # Normalizar el texto extraído
    #print(texto_normalizado)  # Para verificar el texto normalizado
    logging.debug(f"Texto normalizado: {texto_normalizado}")
    
    tipos_examenes = determinar_tipos_examenes(texto_normalizado)  # <-- Llamada a la función para determinar el tipo de examen ***
    #print(tipos_examenes)  # Para verificar los tipos de examen encontrados
    
    if not tipos_examenes:
        logging.warning(f"No se encontraron tipos de examen en el archivo {archivo}.")
        return

    # Cadenas para extraer subcadenas (texto relevante) según el tipo de examen
    cadenas_busqueda = {
        "BASAL": (r"INFORME\s+DE\s+POLISOMNOGRAFIA\s+BASAL", r"Saturacion\s+O2\s+Minima\s+durante\s+el\s+sueno"),
        "CPAP": (r"^", r"CONCLUSION(?:ES)?"),
        "DAM": (r"INFORME\s+DE\s+POLISOMNOGRAFIA\s+BASAL\s+CON\s+DISPOSITIVO\s+(?:DE\s+AVANCE\s+)?MANDIBULAR", r"CONCLUSION(?:ES)?"),
        "BPAP": (r"INFORME\s+DE\s+POLISOMNOGRAFIA\s+EN\s+TITULACION\s+DE\s+B[I]?PAP", r"CONCLUSION(?:ES)?"),
        "ACTIGRAFIA": (r"Fecha", r"ESTADISTICAS DIARIAS"),
        "CAPNOGRAFIA": (r"INFORME\s+DE\s+CAPNOGRAFIA", r"CONCLUSION(?:ES)?"),
        "AUTOCPAP": (r"^", r"Informe\s+de\s+cumplimiento"),
        "POLIGRAFIA": (r"^", r"Indicacion\s+del\s+estudio")
    }

    for tipo in tipos_examenes:
        logging.info(f"Procesando examen de {tipo}")
        if tipo in cadenas_busqueda:
            inicio, fin = cadenas_busqueda[tipo]
            logging.debug(f"Buscando subcadenas para {tipo}: Inicio: {inicio}, Fin: {fin}")
            texto_relevante = extraer_subcadenas(texto_normalizado, inicio, fin) # <-- Llamada a la función para extraer SUBCADENAS ***
            if texto_relevante:
                logging.info(f"Subcadena encontrada para {tipo}: {texto_relevante}")
                
                if tipo == "BASAL":
                    logging.info(f"** INICIO ** Procesando archivo BASAL válido: {archivo}")

                    if extension == ".rtf":
                        resultados_psg = procesar_psg_rtf(texto_relevante, archivo)
                        nombre_archivo = "resultados_psg_rtf.csv"
                    elif extension == ".doc":
                        resultados_psg = procesar_psg_doc(texto_relevante, archivo)
                        nombre_archivo = "resultados_psg_doc.csv"
                    else:
                        logging.warning(f"Extensión no reconocida para archivo: {archivo}")
                        continue

                    directorio_salida = "output"
                    os.makedirs(directorio_salida, exist_ok=True)
                    ruta = os.path.join(directorio_salida, nombre_archivo)

                    es_nuevo = not os.path.isfile(ruta)
                    with open(ruta, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=resultados_psg.keys())
                        if es_nuevo:
                            writer.writeheader()
                        writer.writerow(resultados_psg)

                    logging.info(f"** FIN ** Procesamiento Basal terminado para {archivo}")
                    
                '''
                elif tipo == "CPAP":
                    logging.info(f"** INICIO ** Procesando archivo CPAP válido: {archivo}")
                    
                    if extension == ".rtf":
                        resultados_cpap = procesar_cpap_rtf(texto_relevante)
                        ruta = "resultados_cpap_rtf.csv"
                    elif extension == ".doc":
                        resultados_cpap = procesar_cpap_doc(texto_relevante)
                        ruta = "resultados_cpap_doc.csv"
                    elif extension == ".docx":
                        resultados_cpap = procesar_cpap_docx(texto_relevante)
                        ruta = "resultados_cpap_docx.csv"
                    else:
                        logging.warning(f"Extensión no reconocida para archivo: {archivo}")
                        continue
                    
                    es_nuevo = not os.path.isfile(ruta)
                    with open(ruta, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=resultados_cpap.keys()) 
                        if es_nuevo:
                            writer.writeheader()
                        writer.writerow(resultados_cpap)
                    logging.info(f"** FIN ** Procesamiento CPAP terminado para {archivo}")

                elif tipo == "DAM": 
                    logging.info(f"** INICIO ** Procesando archivo DAM válido: {archivo}")
                    if extension == ".rtf":
                        resultados_dam = procesar_dam_rtf(texto_relevante)
                        ruta = "resultados_dam_rtf.csv"
                    elif extension == ".doc":   
                        resultados_dam = procesar_dam_doc(texto_relevante)
                        ruta = "resultados_dam_doc.csv"
                    else:
                        logging.warning(f"Extensión no reconocida para archivo: {archivo}")
                        continue
                    es_nuevo = not os.path.isfile(ruta)
                    with open(ruta, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=resultados_dam.keys()) 
                        if es_nuevo:
                            writer.writeheader()
                        writer.writerow(resultados_dam)
                    logging.info(f"** FIN ** Procesamiento DAM terminado para {archivo}")

                elif tipo == "BPAP": 
                    logging.info(f"** INICIO ** Procesando archivo BPAP válido: {archivo}")
                    if extension == ".rtf":
                        resultados_bpap = procesar_bpap_rtf(texto_relevante)
                        ruta = "resultados_bpap_rtf.csv"
                    elif extension == ".doc":
                        resultados_bpap = procesar_bpap_doc(texto_relevante)
                        ruta = "resultados_bpap_doc.csv"
                    else:
                        logging.warning(f"Extensión no reconocida para archivo: {archivo}")
                        continue
                    es_nuevo = not os.path.isfile(ruta)
                    with open(ruta, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=resultados_bpap.keys()) 
                        if es_nuevo:
                            writer.writeheader()
                        writer.writerow(resultados_bpap)
                    logging.info(f"** FIN ** Procesamiento BPAP terminado para {archivo}")

                elif tipo == "ACTIGRAFIA":
                    logging.info(f"** INICIO ** Procesando archivo ACTIGRAFIA válido: {archivo}")
                    if extension == ".doc":
                        resultados_actigrafia = procesar_actigrafia_doc(texto_relevante)
                        ruta = "resultados_actigrafia_doc.csv"
                    else:
                        logging.warning(f"Extensión no reconocida para archivo: {archivo}")
                        continue
                    es_nuevo = not os.path.isfile(ruta)
                    with open(ruta, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=resultados_actigrafia.keys()) 
                        if es_nuevo:
                            writer.writeheader()
                        writer.writerow(resultados_actigrafia)
                    logging.info(f"** FIN ** Procesamiento BPAP terminado para {archivo}")

                elif tipo == "CAPNOGRAFIA":
                    logging.info(f"** INICIO ** Procesando archivo CAPNOGRAFIA válido: {archivo}")
                    if extension == ".rtf":
                        resultados_capnografia = procesar_capnografia_rtf(texto_relevante)
                        ruta = "resultados_capnografia_rtf.csv"
                    elif extension == ".doc":
                        resultados_capnografia = procesar_capnografia_doc(texto_relevante)
                        ruta = "resultados_capnografia_doc.csv"
                    else:
                        logging.warning(f"Extensión no reconocida para archivo: {archivo}")
                        continue
                    es_nuevo = not os.path.isfile(ruta)
                    with open(ruta, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=resultados_capnografia.keys()) 
                        if es_nuevo:
                            writer.writeheader()
                        writer.writerow(resultados_capnografia)
                    logging.info(f"** FIN ** Procesamiento BPAP terminado para {archivo}")

                                
                elif tipo == "AUTOCPAP":
                    logging.info(f"** INICIO ** Procesando archivo AUTOCPAP válido: {archivo}")
                    if extension == ".docx":
                        resultados_autocpap = procesar_autocpap_docx(texto_relevante)
                        ruta = "resultados_autocpap_docx.csv"
                    else:
                        logging.warning(f"Extensión no reconocida para archivo: {archivo}")
                        continue
                    es_nuevo = not os.path.isfile(ruta)
                    with open(ruta, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=resultados_autocpap.keys()) 
                        if es_nuevo:
                            writer.writeheader()
                        writer.writerow(resultados_autocpap)
                    logging.info(f"** FIN ** Procesamiento AUTOCPAP terminado para {archivo}")

                
                if tipo == "POLIGRAFIA":
                    logging.info(f"** INICIO ** Procesando archivo POLIGRAFIA válido: {archivo}")
                    if extension == ".docx":
                        resultados_poligrafia = procesar_poligrafia_docx(texto_relevante)
                        ruta = "resultados_poligrafia_docx.csv"
                    else:
                        logging.warning(f"Extensión no reconocida para archivo: {archivo}")
                        continue
                    es_nuevo = not os.path.isfile(ruta)
                    with open(ruta, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=resultados_poligrafia.keys()) 
                        if es_nuevo:
                            writer.writeheader()
                        writer.writerow(resultados_poligrafia)
                    logging.info(f"** FIN ** Procesamiento POLIGRAFIA terminado para {archivo}")
                '''
            else:
                logging.error(f"No se encontraron subcadenas para {tipo} en el archivo {archivo}.")
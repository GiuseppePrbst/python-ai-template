"""Paquete ``audit``.

Implementa el subcomando ``python-ai-template audit <repository>``.
Es estrictamente read-only respecto del repositorio auditado: no crea
archivos, temporales ni directorios dentro del target.

Modulos:
    - cli: argparse y orquestacion.
    - scanner: recorrido read-only del filesystem y Git.
    - classifier: deteccion de senales y arquetipo.
    - render: renderer TOML determinista limitado al schema.
    - model: dataclasses inmutables del schema.

Los submodulos se importan de forma diferida (dentro de funciones)
para evitar dependencias circulares y costos de importacion. Por eso
``__all__`` se omite: pyright exige que los nombres listados esten
presentes en el modulo, y al ser importacion diferida no lo estan
hasta que se invoca la funcion que los usa.
"""

from __future__ import annotations

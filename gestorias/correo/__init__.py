# -*- coding: utf-8 -*-
"""
Módulo de correo de GestorIA.

El dolor (verbatim de prospectos): "recibimos infinidad de correos con
facturas para el trimestre". Este módulo lee la bandeja (IMAP real o carpeta
.eml de demo), clasifica cada correo (factura / requerimiento / documentación /
consulta / comercial), prioriza, y pasa las facturas adjuntas por el extractor
automáticamente → CSV listo para A3/Sage/Holded.
"""

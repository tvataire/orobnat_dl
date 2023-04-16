#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import traceback
from logger import logger
from orobnat import ReportExporter, HTMLStrategy, PDFStrategy, Session, ReportIterator
from argparse import ArgumentParser, RawTextHelpFormatter, ArgumentError, SUPPRESS

EXPORT_FORMATS = {'PDF': PDFStrategy, 'HTML': HTMLStrategy}
DEFAULT_EXPORT_FORMAT = list(EXPORT_FORMATS.keys())[0]


def dl_reports(session, **kwargs):
    """
    Download all reports for given "region", "departement", "commune" and "reseau".
    :param session: An orobnat.Session instance.
    :param kwargs: Misc params retrieved from command line.
    """
    exporter = ReportExporter(kwargs['CHEMIN'], [EXPORT_FORMATS[a_format] for a_format in kwargs['format']])
    req_data = {'methode': 'rechercher',
                'idRegion': kwargs['region'],
                'usd': 'AEP',
                'posPLV': 0,
                'departement': kwargs['departement'],
                'communeDepartement': kwargs['commune'],
                'reseau': kwargs['reseau']}

    for report in ReportIterator(session, req_data):
        logger.info('Export report : {}'.format(report['date du prélèvement']))
        exporter.export(report)


def print_items(session, **kwargs):
    """
    Print all items from a given "region", "departement" or "commune".
    :param session: An orobnat.Session instance.
    :param kwargs: Misc params retrieved from command line.
    """
    messages = {'liste_departements': 'Départements disponibles pour cette région :\n',
                'liste_communes': 'Communes disponibles pour ce département :\n',
                'liste_reseaux': 'Reseaux disponibles pour cette commune :\n'}
    items = {'liste_departements': 'departements',
             'liste_communes': 'communes',
             'liste_reseaux': 'reseaux'}
    key = {kwargs[key]: key for key in messages}[True]
    print('{}{}'.format(messages[key],
                        '\n'.join(['{}: {}'.format(key, value)
                                   for key, value in getattr(session, items[key]).items()])))


def main():
    s_args = dict()
    session = Session(s_args)
    try:
        parser = ArgumentParser(description='Cet outil permet de télécharger les résultats d\'analyse d\'eau potable '
                                            'depuis le site https://orobnat.sante.gouv.fr',
                                formatter_class=RawTextHelpFormatter,
                                add_help=False)
        parser.add_argument('-h', '--help', action='help', default=SUPPRESS,
                            help='Afficher ce message d\'aide.')
        parser.add_argument('--debug', help='Afficher les informations de débogage.', action='store_true')
        parser.add_argument('--dry-run', help='Afficher les actions à réaliser mais ne rien faire.',
                            action='store_true')
        parser.add_argument('--format', help='Sélectionner le format d\'export.\nDéfault : {}'.format(
            DEFAULT_EXPORT_FORMAT), nargs='*', choices=EXPORT_FORMATS.keys(),
                            default=[DEFAULT_EXPORT_FORMAT])
        regions = session.regions
        region = parser.add_argument('--region',
                                     help='Sélectionner une région : \n{}'.format('\n'.join(['{}: {}'.format(key, value)
                                                                                             for key, value in
                                                                                             regions.items()])),
                                     choices=regions.keys(), metavar='ID')
        # --liste-departementsn, --liste-communes, --liste-reseaux are mutually exclusive.
        group = parser.add_mutually_exclusive_group()
        departements = group.add_argument('--liste-departements',
                                          help='Afficher la liste des départements disponibles pour la région '
                                               'sélectionnée.',
                                          action='store_true')
        departement = parser.add_argument('--departement', help='Sélectionner un département.', metavar='ID')
        communes = group.add_argument('--liste-communes',
                                      help='Afficher la liste des communes disponibles pour le département '
                                           'sélectionné.',
                                      action='store_true')
        commune = parser.add_argument('--commune', help='Sélectionner une commune.', metavar='ID')
        reseaux = group.add_argument('--liste-reseaux',
                                     help='Afficher la liste des réseaux disponibles pour la commune '
                                          'sélectionnée.',
                                     action='store_true')
        reseau = group.add_argument('--reseau', help='Sélectionner un réseau.', metavar='ID')
        chemin = parser.add_argument('CHEMIN', help='Chemin du répertoire d\'export.', nargs='?')
        args = parser.parse_args()
        if args.debug:
            logger.setLevel('DEBUG')
        logger.debug('Parsed args : {}'.format(args))
        if args.dry_run:
            args.format.clear()
        d_args = vars(args)
        # update session with command-line arguments
        s_args.update(d_args)
        command = dl_reports
        try:
            if args.liste_departements:
                if None is args.region:
                    raise ArgumentError(departements,
                                        'Veuillez sélectionner une région pour afficher la liste des départements.')
                command = print_items
            if args.departement is not None:
                if args.departement not in session.departements.keys():
                    raise ArgumentError(departement, 'Le département {} ne se trouve pas dans la région {}.'.format(
                        args.departement, regions[args.region]))
            if args.liste_communes:
                if (None is args.region) or (None is args.departement):
                    raise ArgumentError(communes,
                                        'Veuillez sélectionner une région et un département pour afficher la liste '
                                        'des communes.')
                command = print_items
            if args.commune is not None:
                if args.commune not in session.communes.keys():
                    raise ArgumentError(commune, 'La commune {} ne se trouve pas dans le département {}.'.format(
                        args.commune, session.departements[args.departement]))
            if args.liste_reseaux:
                if (None is args.region) or (None is args.departement) or (None is args.commune):
                    raise ArgumentError(reseaux,
                                        'Veuillez sélectionner une région, un département et une commune pour afficher '
                                        'la liste des réseaux.')
                command = print_items
            if args.reseau is not None:
                if args.reseau not in session.reseaux.keys():
                    raise ArgumentError(commune, 'Le réseau {} n\'est pas disponible dans la commune {}.'.format(
                        args.reseau, session.communes[args.commune]))
            if command == dl_reports:
                mandatory_args = [region, departement, commune, reseau, chemin]
                for arg in mandatory_args:
                    if None is d_args[arg.dest]:
                        raise ArgumentError(arg,
                                            'Le paramètre \'{}\' est nécessaire pour téléchager les rapports '
                                            'd\'analyse.'.format(arg.dest))
        except ArgumentError as ae:
            raise parser.error(ae.message)
        logger.debug('Command : {}, Arguments: {}'.format(command.__name__, s_args))
        command(session, **s_args)
    finally:
        session.close()


if __name__ == '__main__':
    try:
        main()
    except Exception:  # noqa
        logger.error(traceback.format_exc())

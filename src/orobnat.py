# -*- coding: utf-8 -*-

from requests import Session as BaseSession
from bs4 import BeautifulSoup
import pdfkit
import re
from datetime import datetime
import os
from abc import ABC, abstractmethod
from collections.abc import Mapping, Iterator


class Session(BaseSession):
    """
    An HTTP Session object which allows to keep certain parameters persistent across requests like cookies.
    """

    URL_REGIONS = 'https://sante.gouv.fr/sante-et-environnement/eaux/eau'
    URL_BASE = 'https://orobnat.sante.gouv.fr/orobnat/afficherPage.do'
    URL_RECHERCHE = 'https://orobnat.sante.gouv.fr/orobnat/rechercherResultatQualite.do'

    def __init__(self, args):
        """
        :param args: A dict which may contains any useful information to be used across the session.
                     This dict may be updated whenever.
        """
        super(Session, self).__init__()
        self.__args = args
        res = self.get('{}?methode=menu&usd=AEP&idRegion=27'.format(self.URL_BASE))
        res.close()
        self.__regions = dict()
        res = self.get(self.URL_REGIONS)
        try:
            soup = BeautifulSoup(res.text, 'html.parser')
            for elem in soup.find('blockquote', attrs=['spip']).find_all('a', attrs=['spip_out']):
                self.__regions[re.sub(r'.+?idRegion=(\d+)$', r'\1', elem['href'])] = elem.get_text()
        finally:
            res.close()

    @property
    def payload_base(self):
        """
        :return: dict : Default data to use with POST requests sent to
                        https://orobnat.sante.gouv.fr/orobnat/rechercherResultatQualite.do
        """
        return {'methode': '',
                'idRegion': '',
                'usd': 'AEP',
                'posPLV': 0,
                'departement': '',
                'communeDepartement': '',
                'reseau': ''}.copy()

    @property
    def regions(self):
        """
        :return: A dict of available "regions" {id: name}
        """
        return self.__regions.copy()

    @property
    def departements(self):
        """
        :return: A dict of available "departements" {id: name}
        """
        result = dict()
        res = self.get('{}?methode=menu&usd=AEP&idRegion={}'.format(self.URL_BASE, self.__args['region']))
        try:
            soup = BeautifulSoup(res.text, 'html.parser')
            for elem in soup.find('select', {'name': 'departement'}).find_all('option'):
                result[elem['value']] = elem.get_text()
        finally:
            res.close()
        return result

    @property
    def communes(self):
        """
        :return: A dict of available "communes" {id: name}
        """
        result = dict()
        res = self.post(self.URL_RECHERCHE, {**self.payload_base,
                                             **{'methode': 'changerDepartement',
                                                'idRegion': self.__args['region'],
                                                'departement': self.__args['departement']}})
        try:
            soup = BeautifulSoup(res.text, 'html.parser')
            for elem in soup.find('select', {'name': 'communeDepartement'}).find_all('option'):
                result[elem['value']] = elem.get_text()
        finally:
            res.close()
        return result

    @property
    def reseaux(self):
        """
        :return: A dict of available "reseaux" {id: name}
        """
        result = dict()
        res = self.post(self.URL_RECHERCHE, {**self.payload_base,
                                             **{'methode': 'changerReseau',
                                                'idRegion': self.__args['region'],
                                                'departement': self.__args['departement'],
                                                'communeDepartement': self.__args['commune']}})
        try:
            soup = BeautifulSoup(res.text, 'html.parser')
            for elem in soup.find('select', {'name': 'reseau'}).find_all('option'):
                result[elem['value']] = elem.get_text()
        finally:
            res.close()
        return result

    def dl_report(self, data):
        """
        Download a report.
        :param data: dict : Payload for the POST requests, derived from payload_base.
        :return: str : HTML content of the report.
        """
        res = self.post(self.URL_RECHERCHE, data)
        try:
            soup = BeautifulSoup(res.text, 'html.parser')
        finally:
            res.close()
        blocks = [div for div in soup.find_all('div', attrs='block-content')]
        for block in blocks.copy():
            if len(block.find_all('h3', attrs=['infos', 'common', 'params'])) < 1:
                blocks.remove(block)
        html = '<html><head><META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8"><style>' \
               '.styled-table {' \
               'border-collapse: collapse;' \
               'margin: 25px 0;' \
               'font-size: 0.9em;' \
               'font-family: sans-serif;' \
               'min-width: 400px;' \
               'box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);}' \
               '.styled-table thead tr {' \
               'background-color: #009879;' \
               'color: #ffffff;' \
               'text-align: left;}' \
               '.styled-table th,.styled-table td {' \
               'padding: 12px 15px;}' \
               '.styled-table tbody tr {' \
               'border-bottom: 1px solid #dddddd;}' \
               '.styled-table tbody tr:nth-of-type(even) {' \
               'background-color: #f3f3f3;}' \
               '.styled-table tbody tr:last-of-type {' \
               'border-bottom: 2px solid #009879;}</style></head><body>'
        for block in blocks:
            block.find('table')['class'] = 'styled-table'
            html = '{}{}'.format(html, block)
        return Report('{}{}'.format(html, '</body></html>'))


class InvalidReportException(Exception):
    pass


class Report(Mapping):
    """
    An analysis report. Report properties are accessible though mapping interface.
    """
    def __init__(self, html):
        """
        :param html: HTML content of the report.
        """
        self.__mapping = dict()
        self.__mapping['html'] = html
        soup = BeautifulSoup(self.__mapping['html'], 'html.parser')
        self.__mapping['charset'] = re.sub(r'.*?charset=(.+)', r'\1', soup.find('meta')['content'])
        blocks = [div for div in soup.find_all('div', attrs='block-content')]
        for block in blocks.copy():
            if None is block.find('h3', attrs=['infos']):
                blocks.remove(block)
        if len(blocks) < 1:
            raise InvalidReportException(html)

        data = [re.sub(r'<td>(.*?)</td>', r'\1', td.get_text()) for td in blocks[0].find_all('td')]
        try:
            self.__mapping['date du prélèvement'] = datetime.strptime(data[0].strip(), '%d/%m/%Y %Hh%M')
        except ValueError:
            try:
                self.__mapping['date du prélèvement'] = datetime.strptime(data[0].strip(), '%d/%m/%Y %H:%M')
            except ValueError:
                self.__mapping['date du prélèvement'] = datetime.strptime(re.sub(r'(\d+/\d+/\d+).*', r'\1',
                                                                                 data[0].strip()), '%d/%m/%Y')
        self.__mapping['commune de prélèvement'] = data[1]
        self.__mapping['installation'] = data[2]
        self.__mapping['service public de distribution'] = data[3]
        self.__mapping['responsable de distribution'] = data[4]
        self.__mapping['maître d\'ouvrage'] = data[5]

    def __getitem__(self, key):
        return self.__mapping[key]

    def __len__(self):
        return len(self.__mapping)

    def __iter__(self):
        return iter(self.__mapping)


class ReportIterator(Iterator):
    """
    Iterate over all reports for a given "region", "departement", "commune" and "reseau".
    """
    def __init__(self, session, payload):
        """
        :param session: An orobnat.Session instance.
        :param payload: dict : Payload for the POST requests, derived from payload_base.
        """
        self.__session = session
        self.__payload = payload

    def __next__(self):
        try:
            result = self.__session.dl_report(self.__payload)
            self.__payload['posPLV'] += 1
        except InvalidReportException:
            raise StopIteration
        return result


class ExportStrategy(ABC):
    """
    Base strategy to export reports.
    """
    def __init__(self, export_dir_path):
        """
        :param export_dir_path: The directory path where to export reports
        """
        self._export_dir_path = export_dir_path

    @property
    @abstractmethod
    def suffix(self):
        """
        :return: str : File suffix for the export.
        """
        return ''

    @abstractmethod
    def export(self, report):
        """
        Export a report.
        :param report: Report : The report to export.
        :return:
        """
        pass


class HTMLStrategy(ExportStrategy):
    """
    Strategy for HTML export.
    """
    PREFIX = 'HTML'

    def __init__(self, export_dir_path):
        super(HTMLStrategy, self).__init__(os.path.join(export_dir_path, self.PREFIX))

    @property
    def suffix(self):
        return 'html'

    def export(self, report):
        export_dir_path = os.path.join(self._export_dir_path, report['date du prélèvement'].strftime('%Y'))
        os.makedirs(export_dir_path, exist_ok=True)
        with open(os.path.join(export_dir_path,
                               '{}.{}'.format(report['date du prélèvement'].strftime('%Y-%m-%d_%H%M%S'),
                                              self.suffix)), 'w') as d:
            d.write(report['html'])


class PDFStrategy(ExportStrategy):
    """
    Strategy for PDF export.
    """
    PREFIX = 'PDF'

    def __init__(self, export_dir_path):
        super(PDFStrategy, self).__init__(os.path.join(export_dir_path, self.PREFIX))

    @property
    def suffix(self):
        return 'pdf'

    def export(self, report):
        export_dir_path = os.path.join(self._export_dir_path, report['date du prélèvement'].strftime('%Y'))
        os.makedirs(export_dir_path, exist_ok=True)
        pdfkit.from_string(report['html'],
                           os.path.join(export_dir_path,
                                        '{}.{}'.format(report['date du prélèvement'].strftime('%Y-%m-%d_%H%M%S'),
                                                       self.suffix)),
                           options={'encoding': 'UTF-8'})


class ReportExporter:
    """
    Export a report with several strategies.
    """
    def __init__(self, export_dir_path, strategies=None):
        """
        :param export_dir_path: The directory path where to export reports.
        :param strategies: iterable : Strategies for each export format.
        """
        self.__strategies = set()
        if None is not strategies:
            for strategy in set(strategies):
                self.__strategies.add(strategy(export_dir_path))

    def export(self, report):
        """
        Export a report in all requested formats.
        :param report: Report : The report to export.
        """
        for strategy in self.__strategies:
            strategy.export(report)

import os
import csv
from xlsxwriter.workbook import Workbook

# -----------------------------------------------------------
# ----------- FUNCTIONS DEFINED HERE ------------------------
# -----------------------------------------------------------


class ExcelTools:

    @staticmethod
    def create_var_stats(project_json, logger):
        logger.info("Creating variant stats excel document...")
        var_stats_xlsx = os.path.join(project_json['var_stats_dir'], 'var_stats.xlsx')

        workbook = Workbook(var_stats_xlsx)

        # set formats
        font_size = 9
        font_name = 'Calibri'
        percent_format = workbook.add_format({'num_format': '0.0%', 'font_size' : font_size, 'font_name' : font_name})
        bold = workbook.add_format({'bold': True, 'bg_color': '#D6D6CC', 'font_size' : font_size,
                                    'font_name' : font_name, 'border' : 1})
        normal = workbook.add_format({'font_size' : font_size, 'font_name' : font_name})

        # Create the Project Stats Sheet
        project_var_stats_worksheet = workbook.add_worksheet('Project Stats')
        with open(project_json['project_var_stats_file'], 'rb') as f:
            reader = csv.reader(f)
            for r, row in enumerate(reader):
                for c, col in enumerate(row):

                    if r > 0 and (c == 1 or c == 2):
                        col = int(col)
                    elif r > 0 and c >= 3:
                        col = float(col)

                    if r == 0:
                        project_var_stats_worksheet.write(r, c, col, bold)
                    elif r > 0 and c >= 5:
                        project_var_stats_worksheet.write(r, c, col, percent_format)
                    else:
                        project_var_stats_worksheet.write(r, c, col, normal)

        # Create the Sample Stats Sheet
        sample_var_stats_worksheet = workbook.add_worksheet('Sample Stats')
        with open(project_json['sample_stats_file'], 'rb') as f:
            reader = csv.reader(f)
            for r, row in enumerate(reader):
                for c, col in enumerate(row):

                    if r > 0 and (c == 1):
                        col = int(col)
                    elif r > 0 and c >= 2:
                        col = float(col)

                    if r == 0:
                        sample_var_stats_worksheet.write(r, c, col, bold)
                    elif r > 0 and c >= 4:
                        sample_var_stats_worksheet.write(r, c, col, percent_format)
                    else:
                        sample_var_stats_worksheet.write(r, c, col, normal)

        # Create the Gene Stats Sheet
        gene_var_stats_worksheet = workbook.add_worksheet('Gene Stats')
        with open(project_json['gene_var_stats_file'], 'rb') as f:
            reader = csv.reader(f)
            for r, row in enumerate(reader):
                for c, col in enumerate(row):

                    if r > 0 and (c == 1 or c == 2):
                        col = int(col)
                    elif r > 0 and c >= 3:
                        col = float(col)

                    if r == 0:
                        gene_var_stats_worksheet.write(r, c, col, bold)
                    elif r > 0 and c >= 5:
                        gene_var_stats_worksheet.write(r, c, col, percent_format)
                    else:
                        gene_var_stats_worksheet.write(r, c, col, normal)


        # Create the Unique Variant Stats Sheet
        unique_var_stats_worksheet = workbook.add_worksheet('Unique Variant Stats')
        with open(project_json['unique_var_stats_file'], 'rb') as f:
            reader = csv.reader(f)
            for r, row in enumerate(reader):
                for c, col in enumerate(row):

                    if r > 0 and (c == 1 or c == 6):
                        col = int(col)
                    elif r > 0 and c >= 7:
                        col = float(col)

                    if r == 0:
                        unique_var_stats_worksheet.write(r, c, col, bold)
                    elif r > 0 and c >= 9:
                        unique_var_stats_worksheet.write(r, c, col, percent_format)
                    else:
                        unique_var_stats_worksheet.write(r, c, col, normal)

        # Create the Individual Variant Stats Sheet
        var_stats_worksheet = workbook.add_worksheet('Individual Variant Stats')
        with open(project_json['var_stats_file'], 'rb') as f:
            reader = csv.reader(f)
            for r, row in enumerate(reader):
                for c, col in enumerate(row):

                    if r > 0 and c in [2, 8, 9]:
                        col = int(col)
                    elif r > 0 and c in [7, 10, 11]:
                        col = float(col)

                    if r == 0:
                        var_stats_worksheet.write(r, c, col, bold)
                    else:
                        var_stats_worksheet.write(r, c, col, normal)

        workbook.close()

        return var_stats_xlsx





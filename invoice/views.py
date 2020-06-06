
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import File,InvoiceItem
from rest_framework import generics
from rest_framework import viewsets
from django.shortcuts import get_object_or_404
import sys
import pdfplumber
import tabula
import os

from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import PDFPageAggregator
from pdfminer3.converter import TextConverter
from pdfminer3 import pdfdocument
import io



from .serializers import FileSerializer,NonDigSerializer,ParsedSerializer,ItemSerializer,UpdateSerializer


#UploadView is an api end point for end user who uploads invoice to digitize
#It uses Multipartparser and formparser to parse form data
# it uses file_serializer with pdf validators

class UploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_serializer = FileSerializer(data=request.data)
        if file_serializer.is_valid():
            file_serializer.save()
            return Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#StatusCheck is an api endpoint for enduser who check digitization status using primary key

class StatusCheck(APIView):
    def get(self,request,*args,**kwargs):
        pk = kwargs['pk']
        try:
            entity = File.objects.get(id=pk)
            if entity.digitizaton_status == 'digitization_pending':
                return Response({'invoice_status':entity.digitizaton_status},status=status.HTTP_200_OK)
            if entity.digitizaton_status == 'digitization_complete':
                serialzer = ParsedSerializer(entity)
                return Response(serialzer.data,status=status.HTTP_200_OK)
        except Exception as err:
            return Response(str(err),status=status.HTTP_400_BAD_REQUEST)



# NondigitizeList ia an api endpoint for internal user who needs token authentication to get list of all nondigitize document

class NonDigitizeList(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = File.objects.filter(digitizaton_status='digitization_pending')
    serializer_class = NonDigSerializer

# Digitizelist is an api endpoint for internal user who needs token authentication to get list of all digitize document
class DigitizeList(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = File.objects.filter(digitizaton_status='digitization_complete')
    serializer_class = NonDigSerializer

# function which implement pdfminer to parse pdf text
def pdf_miner_reader(filename):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    try:
        with open(filename, 'rb') as fh:

            for page in PDFPage.get_pages(fh,
                                        caching=True,
                                        check_extractable=True):
                page_interpreter.process_page(page)

            text = fake_file_handle.getvalue()

        # close open handles
        converter.close()
        fake_file_handle.close()
        return text
        
    except pdfdocument.PDFTextExtractionNotAllowed:
        return None

# function which implement pdfplumber to parse pdf text 

def pdf_plumber_reader(filename):
    data = ''
    try:
        with pdfplumber.open(filename) as pdf:
            for content in pdf.pages:
                data += content.extract_text()
        return data
    except TypeError:
        return data

# parse document api for authorized internal user to parse pdf document
# it implements tabula-py to extract tables from pdf
# it implements pdfminer and pdfplumber to extract text from pdf
# I consider 3 cases. first with multiple table pdf,second single table pdf,third pdf with no table
# I uses keyword_test to get almost every keyword specific info from pdf and mapped with File model and InvoiceItem model

class ParseDocument(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request,*args,**kwargs):
        pk = kwargs['pk']
        related_object = File.objects.get(id=pk)
        filename = os.getcwd()+os.sep+'media'+os.sep+str(related_object.file)
        tables = tabula.read_pdf(filename,)
        # print(filename,type(filename))
        item_data_dict = {}
        keyword_dict = {'from':'','to':'','bill to':'','ship to':'','billed to':'','shipped to':'','vender':'','seller':'','invoice':'','invoice date':'','total amount':'','order number':''}
        miner_keyword_list = ['from','to','bill to','ship to','billed to','shipped to','vender','seller','invoice','invoice date','total amount','order number']
        test_keyword_1 = ['item','items','description','service','names','services','name','service description']
        test_keyword_2 = ['qty','quantity','hrs','hours','invoice date','hrs/qty']
        test_keyword_3 = ['price','unit price','rate','rate/price']
        test_keyword_4 = ['total','sub_total','amount']
        if len(tables) == 0:
            text = pdf_miner_reader(filename)
            if text == None:
                text = pdf_plumber_reader(filename)
                text_list = text.split('\n')
                for inner_item in text_list:
                    for keyword_item in miner_keyword_list:
                        if keyword_item in inner_item.lower():
                            inner_text = inner_item.lower().split(keyword_item)[1]
                            if len(keyword_dict[keyword_item]) == 0:
                                keyword_dict[keyword_item] = inner_text

            else:
                text_list = text.split('\n\n')
                for inner_item in text_list:
                    for keyword_item in miner_keyword_list:
                        if keyword_item in inner_item.lower():
                            inner_text = inner_item.lower().split(keyword_item)[1]
                            if len(keyword_dict[keyword_item]) == 0:
                                keyword_dict[keyword_item] = inner_text

            if not(keyword_dict['bill to'] and keyword_dict['ship_to']):
                if not(keyword_dict['billed to'] and keyword_dict['shipped_to']):
                    File.objects.filter(id=pk).update(invoice_from=keyword_dict['from'],to=keyword_dict['to'],bill_to=keyword_dict['bill to'],\
                                                        ship_to=keyword_dict['ship to'],invoice_number=keyword_dict['invoice'],\
                                                    invoice_date = keyword_dict['invoice date'],total_amount=keyword_dict['total amount'],\
                                                    order_number=keyword_dict['order number']  )
                else:
                    File.objects.filter(id=pk).update(invoice_from=keyword_dict['from'],to=keyword_dict['to'],bill_to=keyword_dict['billed to'],\
                                                        ship_to=keyword_dict['shipped to'],invoice_number=keyword_dict['invoice'],\
                                                    invoice_date = keyword_dict['invoice date'],total_amount=keyword_dict['total amount'],\
                                                    order_number=keyword_dict['order number']  )
            else:
                File.objects.filter(id=pk).update(invoice_from=keyword_dict['from'],to=keyword_dict['to'],bill_to=keyword_dict['bill to'],\
                                                        ship_to=keyword_dict['ship to'],invoice_number=keyword_dict['invoice'],\
                                                    invoice_date = keyword_dict['invoice date'],total_amount=keyword_dict['total amount'],\
                                                    order_number=keyword_dict['order number'] )
            updated_file_object = File.objects.get(id=pk)
            outer_keyword_1 = list(filter(lambda x: x in list(item_data_dict.keys()),test_keyword_1))
            outer_keyword_2 = list(filter(lambda x: x in list(item_data_dict.keys()),test_keyword_2))
            outer_keyword_3 = list(filter(lambda x: x in list(item_data_dict.keys()),test_keyword_3))
            outer_keyword_4 = list(filter(lambda x: x in list(item_data_dict.keys()),test_keyword_4))
            # print(outer_keyword_1,outer_keyword_2,outer_keyword_3,outer_keyword_4)
            if outer_keyword_2 != []:
                outer_keyword_2 = outer_keyword_2[0]
            else:
                outer_keyword_2 = ''
            if outer_keyword_3 != []:
                outer_keyword_3 = outer_keyword_3[0]
            else:
                outer_keyword_3  = ''
            if outer_keyword_4 != []:
                outer_keyword_4 = outer_keyword_4[0]
            else:
                outer_keyword_4 = ''
            if outer_keyword_1 != []:
                outer_keyword_1 = outer_keyword_1[0]
                if (outer_keyword_2 and outer_keyword_3 and outer_keyword_4):
                    for index in range(len(item_data_dict[outer_keyword_1])):
                        InvoiceItem.objects.create(File=updated_file_object,item=item_data_dict[outer_keyword_1][index],\
                                quantity=item_data_dict[outer_keyword_2][index],price=item_data_dict[outer_keyword_3][index],\
                                item_total =item_data_dict[outer_keyword_4][index])
                elif (outer_keyword_2 and outer_keyword_3):
                    for index in range(len(item_data_dict[outer_keyword_1])):
                        InvoiceItem.objects.create(File=updated_file_object,item=item_data_dict[outer_keyword_1][index],\
                                quantity=item_data_dict[outer_keyword_2][index],price=item_data_dict[outer_keyword_3][index])
                    
                elif (outer_keyword_3 and outer_keyword_4):
                    for index in range(len(item_data_dict[outer_keyword_1])):
                        InvoiceItem.objects.create(File=updated_file_object,item=item_data_dict[outer_keyword_1][index],\
                            price=item_data_dict[outer_keyword_3][index],item_total =item_data_dict[outer_keyword_4][index])
                elif(outer_keyword_2 and outer_keyword_4):
                    for index in range(len(item_data_dict[outer_keyword_1])):
                        InvoiceItem.objects.create(File=updated_file_object,item=item_data_dict[outer_keyword_1][index],\
                                quantity=item_data_dict[outer_keyword_2][index],item_total =item_data_dict[outer_keyword_4][index])
                else:
                    for index in range(len(item_data_dict[outer_keyword_1])):
                        InvoiceItem.objects.create(File=updated_file_object,item=item_data_dict[outer_keyword_1][index])
            else:
                pass
        else:
            if len(tables) == 1:
                table = tables[0].dropna(axis=1)
                if len(table.columns) != 0:
                    for value in list(table.columns):
                        item_data_dict[value.lower()] = list(table['value'])
    
                text = pdf_miner_reader(filename)
                if text == None:
                    text = pdf_plumber_reader(filename)
                    text_list = text.split('\n')
                    for inner_item in text_list:
                        for keyword_item in miner_keyword_list:
                            if keyword_item in inner_item.lower():
                                inner_text = inner_item.lower().split(keyword_item)[1]
                                if len(keyword_dict[keyword_item]) == 0:
                                    keyword_dict[keyword_item] = inner_text

                else:
                    text_list = text.split('\n\n')
                    for inner_item in text_list:
                        for keyword_item in miner_keyword_list:
                            if keyword_item in inner_item.lower():
                                inner_text = inner_item.lower().split(keyword_item)[1]
                                if len(keyword_dict[keyword_item]) == 0:
                                    keyword_dict[keyword_item] = inner_text

                if not(keyword_dict['bill to'] and keyword_dict['ship_to']):
                    if not(keyword_dict['billed to'] and keyword_dict['shipped_to']):
                        File.objects.filter(id=pk).update(invoice_from=keyword_dict['from'],to=keyword_dict['to'],bill_to=keyword_dict['bill to'],\
                                                            ship_to=keyword_dict['ship to'],invoice_number=keyword_dict['invoice'],\
                                                        invoice_date = keyword_dict['invoice date'],total_amount=keyword_dict['total amount'],\
                                                        order_number=keyword_dict['order number']  )
                    else:
                        File.objects.filter(id=pk).update(invoice_from=keyword_dict['from'],to=keyword_dict['to'],bill_to=keyword_dict['billed to'],\
                                                            ship_to=keyword_dict['shipped to'],invoice_number=keyword_dict['invoice'],\
                                                        invoice_date = keyword_dict['invoice date'],total_amount=keyword_dict['total amount'],\
                                                        order_number=keyword_dict['order number']  )
                else:
                    File.objects.filter(id=pk).update(invoice_from=keyword_dict['from'],to=keyword_dict['to'],bill_to=keyword_dict['bill to'],\
                                                            ship_to=keyword_dict['ship to'],invoice_number=keyword_dict['invoice'],\
                                                        invoice_date = keyword_dict['invoice date'],total_amount=keyword_dict['total amount'],\
                                                        order_number=keyword_dict['order number'] )
                updated_file_object = File.objects.get(id=pk)
                outer_keyword_1 = list(filter(lambda x: x in list(item_data_dict.keys()),test_keyword_1))
                outer_keyword_2 = list(filter(lambda x: x in list(item_data_dict.keys()),test_keyword_2))
                outer_keyword_3 = list(filter(lambda x: x in list(item_data_dict.keys()),test_keyword_3))
                outer_keyword_4 = list(filter(lambda x: x in list(item_data_dict.keys()),test_keyword_4))
                # print(outer_keyword_1,outer_keyword_2,outer_keyword_3,outer_keyword_4)
                if outer_keyword_2 != []:
                    outer_keyword_2 = outer_keyword_2[0]
                else:
                    outer_keyword_2 = ''
                if outer_keyword_3 != []:
                    outer_keyword_3 = outer_keyword_3[0]
                else:
                    outer_keyword_3  = ''
                if outer_keyword_4 != []:
                    outer_keyword_4 = outer_keyword_4[0]
                else:
                    outer_keyword_4 = ''
                if outer_keyword_1 != []:
                    outer_keyword_1 = outer_keyword_1[0]
                    if (outer_keyword_2 and outer_keyword_3 and outer_keyword_4):
                        for index in range(len(item_data_dict[outer_keyword_1])):
                            InvoiceItem.objects.create(File=updated_file_object,item=item_data_dict[outer_keyword_1][index],\
                                    quantity=item_data_dict[outer_keyword_2][index],price=item_data_dict[outer_keyword_3][index],\
                                    item_total =item_data_dict[outer_keyword_4][index])
                    elif (outer_keyword_2 and outer_keyword_3):
                        for index in range(len(item_data_dict[outer_keyword_1])):
                            InvoiceItem.objects.create(File=updated_file_object,item=item_data_dict[outer_keyword_1][index],\
                                    quantity=item_data_dict[outer_keyword_2][index],price=item_data_dict[outer_keyword_3][index])
                        
                    elif (outer_keyword_3 and outer_keyword_4):
                        for index in range(len(item_data_dict[outer_keyword_1])):
                            InvoiceItem.objects.create(File=updated_file_object,item=item_data_dict[outer_keyword_1][index],\
                                price=item_data_dict[outer_keyword_3][index],item_total =item_data_dict[outer_keyword_4][index])
                    elif(outer_keyword_2 and outer_keyword_4):
                        for index in range(len(item_data_dict[outer_keyword_1])):
                            InvoiceItem.objects.create(File=updated_file_object,item=item_data_dict[outer_keyword_1][index],\
                                    quantity=item_data_dict[outer_keyword_2][index],item_total =item_data_dict[outer_keyword_4][index])
                    else:
                        for index in range(len(item_data_dict[outer_keyword_1])):
                            InvoiceItem.objects.create(File=updated_file_object,item=item_data_dict[outer_keyword_1][index])
                else:
                    pass

            else:
                for table in tables:
                    for value in list(table.columns):
                        item_data_dict[value.lower()] = list(table[value])

                text = pdf_miner_reader(filename)
                if text == None:
                    text = pdf_plumber_reader(filename)
                    text_list = text.split('\n')
                    for inner_item in text_list:
                        for keyword_item in miner_keyword_list:
                            if keyword_item in inner_item.lower():
                                inner_text = inner_item.lower().split(keyword_item)[1]
                                if len(keyword_dict[keyword_item]) == 0:
                                    keyword_dict[keyword_item] = inner_text
                else:
                    text_list = text.split('\n\n')
                    for inner_item in text_list:
                        for keyword_item in miner_keyword_list:
                            if keyword_item in inner_item.lower():
                                inner_text = inner_item.lower().split(keyword_item)[1]
                                if len(keyword_dict[keyword_item]) == 0:
                                    keyword_dict[keyword_item] = inner_text 

                if not(keyword_dict['bill to'] and keyword_dict['ship_to']):
                        if not(keyword_dict['billed to'] and keyword_dict['shipped_to']):
                            File.objects.filter(id=pk).update(invoice_from=keyword_dict['from'],to=keyword_dict['to'],bill_to=keyword_dict['bill to'],\
                                                              ship_to=keyword_dict['ship to'],invoice_number=keyword_dict['invoice'],\
                                                            invoice_date = keyword_dict['invoice date'],total_amount=keyword_dict['total amount'],\
                                                            order_number=keyword_dict['order number']  )
                        else:
                            File.objects.filter(id=pk).update(invoice_from=keyword_dict['from'],to=keyword_dict['to'],bill_to=keyword_dict['billed to'],\
                                                              ship_to=keyword_dict['shipped to'],invoice_number=keyword_dict['invoice'],\
                                                            invoice_date = keyword_dict['invoice date'],total_amount=keyword_dict['total amount'],\
                                                            order_number=keyword_dict['order number']  )
                else:
                    File.objects.filter(id=pk).update(invoice_from=keyword_dict['from'],to=keyword_dict['to'],bill_to=keyword_dict['bill to'],\
                                                              ship_to=keyword_dict['ship to'],invoice_number=keyword_dict['invoice'],\
                                                            invoice_date = keyword_dict['invoice date'],total_amount=keyword_dict['total amount'],\
                                                            order_number=keyword_dict['order number'] )
                updated_file_object = File.objects.get(id=pk)
                outer_keyword_1 = list(filter(lambda x: x in list(item_data_dict.keys()),test_keyword_1))
                outer_keyword_2 = list(filter(lambda x: x in list(item_data_dict.keys()),test_keyword_2))
                outer_keyword_3 = list(filter(lambda x: x in list(item_data_dict.keys()),test_keyword_3))
                outer_keyword_4 = list(filter(lambda x: x in list(item_data_dict.keys()),test_keyword_4))
                if outer_keyword_2 != []:
                    outer_keyword_2 = outer_keyword_2[0]
                else:
                    outer_keyword_2 = ''
                if outer_keyword_3 != []:
                    outer_keyword_3 = outer_keyword_3[0]
                else:
                    outer_keyword_3  = ''
                if outer_keyword_4 != []:
                    outer_keyword_4 = outer_keyword_4[0]
                else:
                    outer_keyword_4 = ''
                if outer_keyword_1 != []:
                    outer_keyword_1 = outer_keyword_1[0]
                    if (outer_keyword_2 and outer_keyword_3 and outer_keyword_4):
                        for index in range(len(item_data_dict[outer_keyword_1])):
                            InvoiceItem.objects.create(File=updated_file_object,item=item_data_dict[outer_keyword_1][index],\
                                    quantity=item_data_dict[outer_keyword_2][index],price=item_data_dict[outer_keyword_3][index],\
                                    item_total =item_data_dict[outer_keyword_4][index])
                    elif (outer_keyword_2 and outer_keyword_3):
                        for index in range(len(item_data_dict[outer_keyword_1])):
                            InvoiceItem.objects.create(File=updated_file_object,item=item_data_dict[outer_keyword_1][index],\
                                    quantity=item_data_dict[outer_keyword_2][index],price=item_data_dict[outer_keyword_3][index])
                        
                    elif (outer_keyword_3 and outer_keyword_4):
                        for index in range(len(item_data_dict[outer_keyword_1])):
                            InvoiceItem.objects.create(File=updated_file_object,item=item_data_dict[outer_keyword_1][index],\
                                price=item_data_dict[outer_keyword_3][index],item_total =item_data_dict[outer_keyword_4][index])
                    elif(outer_keyword_2 and outer_keyword_4):
                        for index in range(len(item_data_dict[outer_keyword_1])):
                            InvoiceItem.objects.create(File=updated_file_object,item=item_data_dict[outer_keyword_1][index],\
                                    quantity=item_data_dict[outer_keyword_2][index],item_total =item_data_dict[outer_keyword_4][index])
                    else:
                        for index in range(len(item_data_dict[outer_keyword_1])):
                            InvoiceItem.objects.create(File=updated_file_object,item=item_data_dict[outer_keyword_1][index])


                
        return Response("Document successfully parsed.",status=status.HTTP_200_OK)

# ParseDocumentView is an api for authorized internal user to see details after parsing of document

class ParsedDocumentView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request,*args,**kwargs):
        pk = kwargs['pk']
        data1 = File.objects.get(id=pk)
        serializer = ParsedSerializer(data1,context={'request':request})

        return Response(serializer.data, status=status.HTTP_200_OK)

#UpdateDocument is an api for internal user to update deatils of document to digitize any document

class UpdateDocument(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = File.objects.all()
    serializer_class = ParsedSerializer
    def put(self,request,*args,**kwargs):
        return self.partial_update(request, *args, **kwargs)

#digitizeDocument api is to mark any document digitize after parsing and updation(if required)

class DigitizeDocument(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = File.objects.all()
    serializer_class = ParsedSerializer
    def put(self,request,*args,**kwargs):
        pk = kwargs['pk']
        File.objects.filter(id=pk).update(digitizaton_status='digitization_complete')
        return Response('document digitization accomplished', status=status.HTTP_200_OK)







        

    

            




        


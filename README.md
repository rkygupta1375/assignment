# Assignment
# Other Dependencies:->
             1) jdk > 8
             2) install other dependencies using requirement.txt
             
# Normal User Api Endpoint:-> 

              1) upload pdf invoice->   url =>   **localhost:8000/invoices/upload/**
                                        method => Post
                                        method body = > variable => "file" (of type file)
                                        
               2) View Status of upload invoice using primary key =>   url => localhost:8000/invoices/status/primary key of uploaded file/
                                                                      eg :=> localhost:8000/invoices/status/1/
                                                                      method => Get
                                          
# Internal User Api Endpoint : -> Token authentication is required to access internal user end point which require user's username and                                        password. " Add token into each request header to access internal user endpoint"
                                # Eg => into header
                                       variable =>   Authorization,   value => token bcvyuwdw5347873bjbcjb

                 1) Generate Token for authentication => url => localhost:8000/api-token-auth/
                                                          method => Post
                                                          method body => 1 variable => username
                                                                          2 variable => password
                                                                          
                 2) View  Non digitalize file list =>  url => localhost:8000/invoices/non-digitizelist/
                                                       method  => Get
                                                       
                 3) View Digitalize file list  =>   url => localhost:8000/invoices/digitize-list/
                                                     method   => Get
                                                     
                 4) Parse Invoice document    =>    url => localhost:8000/invoices/parse/pk/
                                                    eg =>  localhost:8000/invoices/parse/1/
                                                    method = Get
                                                    
                 5) View Parse Invoice data    =>   url => localhost:8000/invoices/view-parse-detail/pk/
                                                    method = Get
                                                    
                 6) Update Fields of parsed file  =>  url => localhost:8000/invoices/update-document/pk/
                                                      method  = Put
                                                      method body  =>  variables which can be update are: => 'invoice_from','to',
                                                                        'file','invoice_number','invoice_date','bill_to','ship_to',
                                                                        'order_number' etc.
                                                                        
                 7) Mark document digitize   =>     url => localhost:8000/invoices/digitize-document/pk/
                                                    method  = Put
                                                     
  # Create internal user using command =>  python manage.py createsuperuser
  
  # start WSGI server using  command =>  python manage.py runserver
  
  # To Generate database table , run these commands in respective order =>  
                                                      1) python manage.py migrate
                                                      2) python manage.py makemigrations
                                                      3) pyhton manage.py migrate
                                          
                 
                 
                 
                 
                 
                                                       
                    

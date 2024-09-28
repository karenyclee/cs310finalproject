# CS 310 Final Project: Serverless IKEA Shopping Cart
Bhavi Barnwal, Karen Lee

## Project Overview 
Our project aims to create a serverless design for a comprehensive IKEA online shopping experience that uses different functionalities from AWS services, including Lambda functions, S3 buckets, and API Gateway. Below is an overview of the key components and functionalities of our project.

## AWS Components
### RDS  
Our database, named *ikeaapp*, contains two tables: products and cart.   
Products is a table of all IKEA US inventory, created using an SQL query and Python file *initialize\_db.py* to convert a Kaggle JSON dataset1 to an SQL query using *datatier*. This mimics how IKEA, as a client and also the server manager, would insert new products in their inventory by directly interacting with the server through a combination of SQL and Python. 

Cart is a table of inventory that the client has reported interest in (i.e. a shopping cart). It contains information about the products, which are collected through the *upload* function. Items are removed from the cart through the *remove* function. See “Lambda” for more information about functions.

### S3  
The S3 bucket is the same one created during Project 2 (*photoapp-nu-cs310-bhavi-barnwal*), but all files related to this project are stored in a folder called *ikeaapp* (similar to the *benfordapp* folder in Project 3). Inside the *ikeaapp* folder, there are original JPG/JPEG images of products the client wants for their shopping cart. In the interior folder *cart\_ikeaapp*, there are thumbnails (created through the *compute* function) to all the product images originally added by the client to the shopping cart through the *upload* function. See “Lambda” for more information about functions.

### API Gateway  
The API Gateway consists of six resources with a method each for the six call-driven functions: *recommend*, *get\_product\_url*, *upload*, *list*, *remove*, and *download*. The functions *get\_product\_url* and *download* use GET methods since they request data (not modify) and do not take user parameters. The remaining functions use POST methods since they take parameters and accordingly create or update S3 and/or RDS.

### Lambda

1. **ikea\_compute**  
   Description: This is an event-driven function triggered automatically whenever a .jpg or .jpeg image is uploaded to the S3 bucket. The code obtains the bucketkey for the image dropped into S3, downloads the image to a temporary local file system (*tmp*), and finally shrinks the image to a thumbnail as a .png file. A Pillow layer was created and added to this Lambda function for image processing. The thumbnail file format is distinct from the original format to prevent an infinite recursive loop occurring due to new JPG files endlessly appearing. The thumbnail file is written to the temporary local file system and then uploaded to S3 inside the *ikeaapp/cart\_ikeaapp* folder, which acts as a shopping cart. The *cart* table inside RDS is simultaneously updated with this newly added product.  
     
   Client: None

2. **ikea\_recommend**  
   Description: The client enters keywords for the product they are looking for, and the maximum price that they are comfortable with paying. With the keywords from the search and the user’s budget in mind, the server looks for the products that are the best match. The server returns a list of all the products (their ID and URL) that best match the criteria in order by how many words matched with the search.   
     
   Client: The client app prints the list of product IDs and URLs for the recommended products, 5 products at a time (unless there aren’t 5 to begin with). The user can choose to continue and look at the next 5 recommended products when prompted to do so. When there are no more recommended products left, the client service returns a message saying “no more recommended products…”.  
     
3. **ikea\_get\_product\_url**  
   Description: Given a product ID, the server retrieves the product URL using an SQL query on the *products* table in RDS to see more information about the product.  
     
   Client: The client is prompted for a product ID that they want to know more about. They receive a link to the product on IKEA’s website in return.  
     
4. **ikea\_upload**  
   Description: Given a local filename for a .jpg or .jpeg image of a product, as well as its product ID, this function uploads the image to “cart” in S3. The server searches through the database, and finds the row of the product with that product ID, and returns the product ID and response status. The product ID, title, and price are added to the *cart* table in RDS. The event-based function *ikea\_compute* performs a computation to convert the uploaded image to a thumbnail PNG stored in the *cart\_ikeaapp* folder inside S3.  
     
   Client: Before using this function, the client must have an image of their desired IKEA product in .jpg/.jpeg format, as well as its product ID, downloaded to their local environment. The client would be prompted for the local filename and the product ID, which would serve as the function’s server-side parameters. The local file would then be uploaded and the thumbnail produced.

5. **ikea\_list**  
   Description: The server uses an SQL query on the *cart* table in RDS to select all items in the client’s shopping cart and return their ID, name, and price.   
     
   Client: The client service parses the data received from the server and prints it out in a formatted manner. It also calculates the subtotal and total number of items thus far.  
     
6. **ikea\_remove**  
   Description: Given a product ID as input, the server deletes this product from the shopping cart. This means it is removed from both the *cart* table in RDS and the S3 shopping cart folder *ikeaapp/cart\_ikeaapp*.   
     
   Client: The client is prompted for a product ID they want to remove from their shopping cart. If that product ID is not in the shopping cart, they will receive an error message. If the item is removed correctly, the client will receive a success message.  
     
7. **ikea\_download**  
   Description: Using the S3 List\_Objects\_V2 function, the server stores all the files inside *ikeaapp/cart\_ikeaapp*. The server makes a temporary local file system (*tmp/cart\_ikeaapp*) and downloads each file there. Then. a new temporary file path is created for the zip file (*tmp/cart\_ikeaapp.zip*), and the shutil module is used to package the contents in *tmp/cart\_ikeaapp* into a zip file stored in *tmp/cart\_ikeaapp.zip*. Lastly, the zip file is opened to read and store its bytes, which are encoded, decoded, and returned as a response.  
     
   Client: Upon receiving the raw data bytes of the zip file, the client re-encodes and then decodes them to deserialize and display the results. These new bytes are written to the local file “shopping\_cart.zip,” which is stored in the current working directory of the client. There is now a client-accessible zip file containing thumbnails of all the products in the client’s shopping cart\!

from sendWeb3Transaction import Web3Transaction
from config import APP_KEY, CACHE_INTERVAL
from flask import Flask, jsonify, request, render_template, flash
from flask_inputs import Inputs
from wtforms import Form, TextField, validators, SelectField, ValidationError
from wtforms.validators import DataRequired
from threading import Timer
from eth_utils import is_hex_address

#Initializing Flask 
app = Flask(__name__)
app.config['SECRET_KEY'] = APP_KEY

#new Transaction instance and interval time to make sure the prices are up to date
newTx = Web3Transaction()
Timer(CACHE_INTERVAL, newTx.keepCacheWarm).start()

#General parameter validation
class InputValidation(Form):
      def validate_address(form, field):
         address = str(field.data)
         if (not is_hex_address(address)):
             raise ValidationError('Error: Please provide a valid Ethereum address')
      def validate_gas(form, field):
          try:
             gasNeeded =  int(field.data)
             if gasNeeded < 1 or gasNeeded > 8000000:
                 raise ValidationError('Please provide a positive integer between 1 and 8 000 000')
          except ValueError:
             raise ValidationError('Error: Please provide a positive integer')

      def validate_speed(form, field):
           speed = str(field.data)
           speedParams = ['slow','medium','fast']
           if(not speed in str(speedParams)):
               raise ValidationError('Error: Please provide a valid speed parameter (fast, medium or slow)')
 

#Front end validation
class ReusableForm(Form):
     speed = TextField('Speed:', validators=[ InputValidation. validate_speed])
     gasNeeded = TextField('GasNeeded:', validators=[ InputValidation.validate_gas])
     address = TextField('Address:', validators=[ InputValidation.validate_address])

#API Validation
class ApiInputs(Inputs):
    args = {
        'gas_needed': [
            DataRequired('gas_needed parameter is missing or incorrect'),
            InputValidation.validate_gas
        ],
        'tx_speed': [
            DataRequired('tx_speed parameter is missing or incorrect'),
            InputValidation.validate_speed
        ],
        'public_address': [
            DataRequired('public_address parameter is missing or incorrect'),
            InputValidation.validate_address
        ]
        }

# Front end
@app.route('/', methods=['GET', 'POST'])
def home():
 form = ReusableForm(request.form)
 if request.method == 'POST':
     if form.validate():

         gasNeeded = int(request.form['gasNeeded'])
         address = request.form['address']
         speed = request.form['speed']
         response = newTx.sendTransaction(gasNeeded, speed, address)

         flash(response['link'])
     else:
         flash(form.errors, 'Error')
 return render_template('home.html', form=form)


# API endpoint
@app.route('/fill-wallet-for-gas', methods=['GET'])
def returnQuery():
    inputs = ApiInputs(request)
    if not inputs.validate():
        return jsonify(success=False, errors=inputs.errors)
    try:
        gasNeeded = int(request.args.get('gas_needed'))
        address = request.args.get('public_address')
        speed = request.args.get('tx_speed')
        response = newTx.sendTransaction(gasNeeded, speed, address)
        return jsonify(response)
    # handleing Transaction exceptions
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        return jsonify(success=False, errors=message)

#Handling invalid routes
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "page not found"})
#Handling internal server errors
@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"error": "internal server error"})
#Running the app 
if __name__ == '__main__':
    app.run(debug=True, port=8000)


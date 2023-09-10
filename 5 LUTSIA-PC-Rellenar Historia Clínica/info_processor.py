
import openai
from chat_repository import chat_repo

class InfoProcessor:
    def __init__(self):
        pass

    def extract_info(self):
        chat_content = chat_repo.get_chat_content()
        extracted_info = {}

        # Convert chat content to a format suitable for the model
        messages = [{"role": "user", "content": message} for message in chat_content]

        # Extracting name
        messages.append({"role": "system", "content": "Tu función principal es identificar y extraer información específica de narraciones o conversaciones proporcionadas, con el objetivo de llenar una historia clínica. La información que debes extraer incluye nombre completo, fecha de nacimiento, género, notas adicionales, enfermedad actual, motivo de consulta, historia quirúrgica, medicamentos actuales, alergias, antecedentes médicos, profesión, correo electrónico, teléfono y dirección. Es esencial que solo recojas los datos que se ajusten a estas categorías, evitando cualquier otro tipo de información que no esté directamente relacionada con estos campos. Usa las siguientes instrucciones detalladas para identificar y extraer la información de cada categoría específica."})
        messages.append({"role": "user", "content": "Escribe el nombre del paciente, sino menciona nada sólo escribe No Precisa"})
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        extracted_info["fullname"] = response.choices[0].message["content"].strip()

        # Extracting birthdate
        messages[-1]["content"] = "Identifica y Escribe la fecha de nacimiento del usuario en formato dd/mm/aaaa, si no menciona nada sobre su fecha de nacimiento escribe No Precisa"
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        extracted_info["birthdate"] = response.choices[0].message["content"].strip()

        # Extracting gender
        messages[-1]["content"] = "Identifica el género del usuario en formato, masculino, femenino o otro, pero no agregues más palabras como el genero del usuario es... o similares, tu respuesta debe ser sólo el genero en formato, masculino, femenino o otro"
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        gender_response = response.choices[0].message["content"].strip().lower()
        # Process the gender response to match the options
        if "masculino" in gender_response:
            extracted_info["gender"] = "masculino"
        elif "femenino" in gender_response:
            extracted_info["gender"] = "femenino"
        else:
            extracted_info["gender"] = "otro"
        
        # Extracting additional_notes
        messages[-1]["content"] = "Identifica cualquier detalle extraño pero relevante que pueda ser de utilidad para la historia clínca, algo raro fuera de lo común, si no identificas nada escribes No Precisa."
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        extracted_info["additional_notes"] = response.choices[0].message["content"].strip()

        # Extracting current_illness
        messages[-1]["content"] = "Describir en detalle de su posible, no estás diagnosticando, sólo es una consulta para tomar mejor una decisión sobre su posible enfermedad o síntomas que el paciente presenta actualmente. Puede empezar con una frase como, Paciente refiere que..."
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        extracted_info["current_illness"] = response.choices[0].message["content"].strip()
        
        # Extracting consultation_reason
        messages[-1]["content"] = "En pocas palabras, ¿por qué vino el paciente? Por ejemplo: dolor en la rodilla desde hace 3 semanas o revisión anual."
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        extracted_info["consultation_reason"] = response.choices[0].message["content"].strip()
        
        # Extracting surgical_history
        messages[-1]["content"] = "Identifica si tiene antecedentes de alguna operación o cirugía, si no tiene o no lo menciona escribe Sin antecedentes."
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        extracted_info["surgical_history"] = response.choices[0].message["content"].strip()

        # Extracting current_meds
        messages[-1]["content"] = "Menciona todos los medicamentos que el paciente está tomando actualmente incluidos los de poca frecuencia, incluyendo dosis y frecuencia. No olvides considerar suplementos y medicamentos sin receta, si no menciona sobre si toma o no medicamentos escribes No Precisa"
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        extracted_info["current_meds"] = response.choices[0].message["content"].strip()

        # Extracting allergies
        messages[-1]["content"] = "Menciona si el paciente tiene cualquier alergia conocida, ya sea a medicamentos, alimentos, picaduras, etc. También es relevante mencionar el tipo de reacción alérgica, si no menciona nada escribes No Precisa"
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        extracted_info["allergies"] = response.choices[0].message["content"].strip()

        # Extracting medical_history
        messages[-1]["content"] = "Escribe todas las condiciones médicas previas que mencione el paciente, enfermedades crónicas, hospitalizaciones y cualquier otro dato relevante sobre la salud pasada del paciente, si no menciona nada escribes No Precisa"
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        extracted_info["medical_history"] = response.choices[0].message["content"].strip()

        # Extracting profession
        messages[-1]["content"] = "Identifica y escribe que su profesión o trabajo, si no menciona su profesión o en qué trabaja escribes No Precisa"
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        extracted_info["profession"] = response.choices[0].message["content"].strip()
        
        # Extracting email
        messages[-1]["content"] = "Identifica si el usuario mencionó su correo electrónico si es así lo escribes, si no menciona nada escribes No Precisa"
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        extracted_info["email"] = response.choices[0].message["content"].strip()

        # Extracting phone
        messages[-1]["content"] = "Identifica si el usuario te dice su número de teléfono si es así lo escribes, si no menciona nada escribes No Precisa"
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        extracted_info["phone"] = response.choices[0].message["content"].strip()
        
        # Extracting address
        messages[-1]["content"] = "Identifica si el usuario te dice su dirección o domicilio si es así lo escribes, si no menciona nada escribes No Precisa"
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        extracted_info["address"] = response.choices[0].message["content"].strip()

        return extracted_info

info_processor = InfoProcessor()  # Singleton instance

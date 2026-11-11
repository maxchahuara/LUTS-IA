{
  "interactionModel": {
    "languageModel": {
      "invocationName": "modo max",
      "intents": [
        {
          "name": "GptQueryIntent",
          "slots": [{"name": "query", "type": "AMAZON.SearchQuery"}],
          "samples": ["consulta {query}", "pregunta {query}", "necesito saber {query}", "explícame {query}"]
        },
        {
          "name": "SearchIntent",
          "slots": [{"name": "query", "type": "AMAZON.SearchQuery"}],
          "samples": ["busca {query}", "investiga {query}", "busca en internet {query}"]
        },
        {
          "name": "TurnOnIntent",
          "slots": [{"name": "target", "type": "AMAZON.SearchQuery"}],
          "samples": ["enciende {target}", "prende {target}", "activa {target}"]
        },
        {
          "name": "TurnOffIntent",
          "slots": [{"name": "target", "type": "AMAZON.SearchQuery"}],
          "samples": ["apaga {target}", "desactiva {target}"]
        },
        {"name": "ResultIntent", "samples": ["consulta mi resultado", "lee mi resultado", "cómo va mi trabajo", "mi resultado"]},
        {"name": "CancelJobIntent", "samples": ["cancela mi trabajo", "cancela la tarea"]},
        {"name": "AMAZON.CancelIntent", "samples": []},
        {"name": "AMAZON.HelpIntent", "samples": []},
        {"name": "AMAZON.StopIntent", "samples": []},
        {"name": "AMAZON.FallbackIntent", "samples": []},
        {"name": "AMAZON.NavigateHomeIntent", "samples": []}
      ],
      "types": []
    }
  }
}

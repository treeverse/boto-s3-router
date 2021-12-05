from botwo.botwo import BotwoBuilder


def client(client_mapping, profiles):
    """
    Create a Botwo client that routes between boto clients by configuration.

    """
    botwo = BotwoBuilder()
    return botwo.create_client_class(client_mapping, profiles)


# def resource(*args, **kwargs):
    # TODO (issue )

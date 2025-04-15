import graphene
from bot.graphene_ql.graphene_types.django_type_mapping import RequestResponseType
class BaseMutation(graphene.Mutation):
    response = graphene.Field(RequestResponseType)

    @classmethod
    def mutate(cls, root, info, **kwargs):
        # This method can be overridden by specific mutations if needed
        return cls(response=RequestResponseType())

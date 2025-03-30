import rctl2
import yaml

test_input = """
@{
    description = "aaa"
}
var1 = 1
var2: variable = 1

var3: secret["env"] = "asdf"

aws: Provider["aws"] = {
}

myresouce1: Resource["aws_s3_bucket"] = {
    a = 1,
    "b":  2,
}

@{
    description = ""
}
group1 Sequential {
    myresouce2: Resource["aws_s3_bucket"] = {
    }
    myresouce3: Resource["aws_s3_bucket"] = {
    }
}

group2 Parallel {
}

#@asdfasdfasda
#{"description": ""}
#var3: variable["default"] = {
#}
"""


nodes = rctl2.parse(test_input)


dumped = yaml.dump(nodes, sort_keys=False)
print(dumped)

resolved = rctl2.flatten_groups(nodes)
# dumped = yaml.dump(resolved, sort_keys=False)
# print(dumped)
dag = rctl2.make_dag(resolved)

json_str = rctl2.generate_json(dag)
print(json_str)

rctl2.create_html(dag, "dag_viewer.html")

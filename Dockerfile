FROM smartnodefr/pythonligo:latest

COPY . .

WORKDIR /contract

RUN ligo compile contract main/main.mligo > test/Farm.tz

RUN ligo compile contract main/farms.mligo > test/Farms.tz

WORKDIR /contract/test

ENTRYPOINT [ "pytest"]
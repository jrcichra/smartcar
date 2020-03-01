FROM golang:alpine3.11
WORKDIR /tester
RUN apk add g++
ADD ./controller .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o controller .
CMD go test -v
library(shiny)
library(ggplot2)
  library(dplyr)
library(gridExtra)
library(hexbin)
library(party)
library(rpart)
library(rpart.plot)
library(tidyverse)
library(skimr)
library(DataExplorer)
library(pROC)
library(tidyverse)
library(randomForest)
library(caret)
library(e1071)
library(fpc)
library(reshape2)
  


ui_upload <- sidebarLayout(
  sidebarPanel(
    fileInput("file", "Data", buttonLabel = "Upload..."),
    textInput("delim", "DelimiXter (leave blank to guess)", ""),
    numericInput("skip", "Rows to skip", 0, min = 0),
    numericInput("rows", "Rows to preview", 10, min = 1)
  ),
  mainPanel(
    
    h3("Please upload the csv file to complete the data analysis."),
    dataTableOutput("dynamic1"),
    dataTableOutput("dynamic2"),
    dataTableOutput("dynamic3"),
    dataTableOutput("dynamic4"),
    tableOutput("preview2"),
    tableOutput("preview3"),
    tableOutput("preview4"),
    tableOutput("preview5"),
    
  
    sliderInput("height", "height", min = 100, max = 1000, value = 650),
    sliderInput("width", "width", min = 100, max = 1000, value = 800),
    
    plotOutput("plot1", brush = "plot_brush"),
    tableOutput("data1"),
    plotOutput("plot2", brush = "plot_brush"),
    tableOutput("data2"),
    plotOutput("plot3", brush = "plot_brush"),
    tableOutput("data3"),
    plotOutput("plot4", brush = "plot_brush"),
    tableOutput("data4")
    
    
    
    
 
    
  )
)


ui <- fluidPage(
  ui_upload,
  theme = bslib::bs_theme(bootswatch = "united"),
  
)




server <- function(input, output, session) {
  raw <- reactive({
    req(input$file)
    delim <- if (input$delim == "") NULL else input$delim
    vroom::vroom(input$file$datapath, delim = delim, skip = input$skip)
  })
  
  preview1 <- renderTable(head(raw(), input$rows))
  
  output$preview2 <- renderTable(skim((raw())[2]))
  output$preview3 <- renderTable(skim((raw())[5]))
  output$preview4 <- renderTable(skim((raw())[8]))
  output$preview5 <- renderTable(skim((raw())[11]))
  output$Missing1 <- renderPlot(
   
    {
      plot_missing((raw())[2])
    })
  output$Missing2 <- renderPlot(
    
    {
      plot_missing((raw())[5])
    })
  output$Missing3 <- renderPlot(
    
    {
      plot_missing((raw())[8])
    })
  output$Missing4 <- renderPlot(
    
    {
      plot_missing((raw())[11])
    })
  
  
  output$dynamic1 <- renderDataTable((raw())[1:2], options = list(pageLength = 10))
  output$dynamic2 <- renderDataTable((raw())[4:5], options = list(pageLength = 10))
  output$dynamic3 <- renderDataTable((raw())[7:8], options = list(pageLength = 10))
  output$dynamic4 <- renderDataTable((raw())[10:11], options = list(pageLength = 10))
  output$data1 <- renderTable({
    brushedPoints((raw())[1:2], input$plot_brush)
  })
  output$data2 <- renderTable({
    brushedPoints((raw())[4:5], input$plot_brush)
  })
  output$data3 <- renderTable({
    brushedPoints((raw())[7:8], input$plot_brush)
  })
  output$data4 <- renderTable({
    brushedPoints((raw())[10:11], input$plot_brush)
  })
  
  
  
  output$plot1 <- renderPlot(
    width = function() input$width,
    height = function() input$height,
    res = 96,
    
    {
      ggplot((raw())[1:2],aes(x=Number1,y=Length1))+geom_point()
    }
    
  )
  output$data1 <- renderTable({
    brushedPoints((raw())[1:2], input$plot_brush)
  })
  
  output$plot2 <- renderPlot(
    width = function() input$width,
    height = function() input$height,
    res = 96,
    {
      ggplot((raw())[4:5],aes(x=Number2,y=Length2))+geom_point()
    })
  output$data2 <- renderTable({
    brushedPoints((raw())[4:5], input$plot_brush)
  })
  
  output$plot3 <- renderPlot(
    width = function() input$width,
    height = function() input$height,
    res = 96,
    {
      ggplot((raw())[7:8],aes(x=Number3,y=Length3))+geom_point()
    })
  output$data3 <- renderTable({
    brushedPoints((raw())[7:8], input$plot_brush)
  })
  
  output$plot4 <- renderPlot(
    width = function() input$width,
    height = function() input$height,
    res = 96,
    {
      ggplot((raw())[10:11],aes(x=Number4,y=Length4))+geom_point()
    })
  output$data4 <- renderTable({
    brushedPoints((raw())[10:11], input$plot_brush)
  })
  
 

  
}


shinyApp(ui, server)

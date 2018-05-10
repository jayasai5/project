{
  "views": {
    "new-view": {
      "reduce": "_count",
      "map": "function (doc) {   if(doc.sentiment.compound>=0.05){     emit([doc.place,'positive'],doc.sentiment.compound)   }   else if(doc.sentiment.compound<=-0.05){    emit([doc.place,'negative'],doc.sentiment.compound)   }   else{   emit([doc.place, 'neutral'],doc.sentiment.compound)  }}"
    }
  }
}
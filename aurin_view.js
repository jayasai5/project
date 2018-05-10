{
  "views": {
    "new-view": {
      "reduce": "function (keys, values) {\n  total_sum = sum(values)\n  count = values.length\n  return total_sum/count\n}",
      "map": "function (doc) {   if(doc.city!=null && doc.rai_cityadjusted_total_2017_q2!=null && doc.city.indexOf('Greater')!=-1 )  emit(doc.city.substring(8), doc.rai_cityadjusted_total_2017_q2);\n}"
    }
  }
}
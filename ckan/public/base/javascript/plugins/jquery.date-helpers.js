this.jQuery.date = {
  /* A map of date methods to text strings. */
  METHODS: {
    "yyyy": "getUTCFullYear",
    "MM":   "getUTCMonth",
    "dd":   "getUTCDate",
    "HH":   "getUTCHours",
    "mm":   "getUTCMinutes",
    "ss":   "getUTCSeconds",
    "fff":  "getUTCMilliseconds"
  },

  /* Formatting of an ISO8601 compatible date */
  ISO8601: "yyyy-MM-ddTHH:mm:ss.fffZ",

  /* Returns a date string for the format provided.
   *
   * date   - A date object to output.
   * format - A format string in the form "yyyy-MM-dd"
   *
   * Returns a formatted date string.
   */
  format: function (date, format) {
    var map = this.METHODS;

    date = date || new Date();

    function pad(str, exp) {
      str = "" + str;
      exp = exp.replace(/[a-z]/ig, '0');
      return str.length !== exp.length ? exp.slice(str.length) + str : str;
    }

    return format.replace(/([a-zA-Z])\1+/g, function (_, $1) {
      if (map[_]) {
        var value = date[map[_]]();
        if (_ === 'MM') {
          value += 1;
        }
        return pad(value, _);
      }
      return _;
    });
  },

  /* Generates a ISO8061 timestamp. Uses the native methods if available.
   *
   * date - A date object to convert.
   *
   * Examples
   *
   *   var timestamp = jQuery.date.toISOString(new Date());
   *
   * Returns a timestamp string.
   */
  toISOString: function (date) {
    date = date || new Date();

    if (date.toISOString) {
      return date.toISOString();
    } else {
      return this.format(date, this.ISO8061);
    }
  }
};

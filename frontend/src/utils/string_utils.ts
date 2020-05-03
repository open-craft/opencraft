export const toCamelCase = (s: string) => {
  return s.replace(/([-_][a-z])/gi, ($1) => {
    return $1.toUpperCase().replace('-', '').replace('_', '');
  });
};

export const sanitizeErrorFeedback = (input: {
  [key: string]: Array<string>;
}) => {
  // Loop at each error message and join them.
  // Also convert keys from snake_case to camelCase
  const newObject: any = {};

  Object.keys(input).forEach((key) => {
    newObject[toCamelCase(key)] = input[key].join();
  });

  return newObject;
};

export const capitalizeFirstLetter = (str: string) => {
  return str[0].toUpperCase() + str.slice(1);
};

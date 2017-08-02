#ifndef COMM_EXCEPTIONS_HPP
#define COMM_EXCEPTIONS_HPP

#include <exception>

class InvalidInputsException : public std::exception
{
    virtual const char * what() const throw() {
        return "Invalid constructor inputs supplied";
    }
};
#endif // COMM_EXCEPTIONS_HPP

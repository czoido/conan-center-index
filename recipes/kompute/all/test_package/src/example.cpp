#include <iostream>
#include <kompute/Kompute.hpp>

int main() {
    // Create a Kompute Manager with default settings
    kp::Manager mgr;

    // Create Kompute Tensors with initial data
    auto tensorA = mgr.tensor({ 1.0f, 2.0f, 3.0f });
    auto tensorB = mgr.tensor({ 4.0f, 5.0f, 6.0f });

    // Perform a simple addition on the CPU for demonstration
    auto tensorC = mgr.tensor({ 0.0f, 0.0f, 0.0f });
    for (size_t i = 0; i < tensorA->vector().size(); ++i) {
        tensorC->vector()[i] = tensorA->vector()[i] + tensorB->vector()[i];
    }

    // Display the result
    std::cout << "Tensor C (A + B): ";
    for (const auto& val : tensorC->vector()) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    return 0;
}

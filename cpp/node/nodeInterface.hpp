#ifndef NODE_NODE_INTERFACE_HPP
#define NODE_NODE_INTERFACE_HPP

#include <atomic>

namespace node {
    
    class NodeInterface {

        public:

            std::atomic<bool> nodeControlRunFlag;

            /**
             * Default constructor.
             */
            NodeInterface();
            
    };

}

#endif // NODE_NODE_INTERFACE_HPP

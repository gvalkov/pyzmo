(import pyzmo
        [sys [exit]]
        [pyzmo [poll util]])

(defmacro key [codes &rest args]
  `(let [[ecodes (map util.get_ecode_or_fail (util.makelist '~codes))]
         [callback (fn [events] (eval (util.last '(~@args))))]
         [states ["down"]]]
     (when (= (len '(~@args)) 2)
       (setv states (list (map (fn [sym] (.lstrip sym "\uFDD0:"))
                               (util.makelist (first '(~@args)))))))
     (foreach [ecode ecodes]
       ((util.create-decorator pyzmo.key ecode {"states" states}) callback))))

(defmacro chord [codes &rest args]
  `(let [[ecodes (map util.get_ecode_or_fail '~codes)]
         [callback (fn [events] (eval (util.last '(~@args))))]]
     ((util.create_decorator pyzmo.chord (list ecodes) {}) callback)))

(defmacro seq [codes &rest args]
  `(let [[ecodes (map util.get_ecode_or_fail '~codes)]
         [callback (fn [events] (eval (util.last '(~@args))))]]
     ((util.create_decorator pyzmo.keyseq (list ecodes) {}) callback)))

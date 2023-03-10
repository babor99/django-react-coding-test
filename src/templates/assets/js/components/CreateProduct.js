import React, { useState, useEffect } from 'react';
import TagsInput from 'react-tagsinput';
import 'react-tagsinput/react-tagsinput.css';
import Dropzone from 'react-dropzone'
import Cookies from 'js-cookie';
import { jsonToFormData, isNumeric } from './commons/utils';
import { fromPairs } from 'lodash';
import { PRODUCT_URL, CREATE_PRODUCT_URL, GET_PRODUCT_URL, UPDATE_PRODUCT_URL, PRODUCT_IMAGE_URL } from './commons/constants';


const CreateProduct = (props) => {
    const [product, setProduct] = useState({ title: "", sku: "", description: "" })
    const [productId, setProductId] = useState('new')

    const [reRender, setReRender] = useState(false);

    const [images, setImages] = useState([])
    const [previewImages, setPreviewImages] = useState([]);

    const [productVariantPrices, setProductVariantPrices] = useState([])
    const [productVariants, setProductVariants] = useState([
        {
            variant: 1,
            tags: []
        }
    ])

    // console.log('id: ', id)

    useEffect(() => {
        const path = window.location.pathname;
        const pathArr = path.split('/');
        const id = pathArr[pathArr.length - 1];
        setProductId(id);
        console.log('id: ', id);
    }, []);

    useEffect(() => {
        const getProduct = async () => {
            const res = await fetch(`${PRODUCT_URL}${productId}`, {
                method: 'GET',
                headers: {
                    // 'Content-Type': 'application/json'
                    // 'X-CSRFToken': csrftoken,
                },
                // mode: 'same-origin',
            });
            const data = await res.json();
            console.log('res.data: ', data);
            if (data.product) {
                setProduct(data.product);
            }
            const imageArr = []
            if (data?.productimages.length > 0) {
                data.productimages.forEach((item) => {
                    imageArr.push(item);
                });
                setPreviewImages(imageArr);
            }
            if (data.productvariants.length > 0) {
                setProductVariants([...data.productvariants]);
                console.log("productvariants block executed!")
            }
            if (data.productvariant_prices.length > 0) {
                setProductVariantPrices([...data.productvariant_prices])
            }
        }
        if (productId !== 'new' && isNumeric(productId)) {
            getProduct()
        }
    }, [productId, reRender]);

    useEffect(() => {
    }, [previewImages, productVariants, productVariantPrices]);


    const handleProductFieldsChange = (e) => {
        setProduct({
            ...product,
            [e.target.name]: e.target.value
        })
    }

    const handlePriceChange = (e, index) => {
        const updatedProductVariantPrices = [...productVariantPrices];
        updatedProductVariantPrices[index] = {
          ...updatedProductVariantPrices[index],
          price: e.target.value
        };
        setProductVariantPrices(updatedProductVariantPrices);
      }
      
    const handleStockChange = (e, index) => {
    const updatedProductVariantPrices = [...productVariantPrices];
    updatedProductVariantPrices[index] = {
        ...updatedProductVariantPrices[index],
        stock: e.target.value
    };
    setProductVariantPrices(updatedProductVariantPrices);
    }



    // handle click event of the Add button
    const handleAddClick = () => {
        let all_variants = JSON.parse(props.variants.replaceAll("'", '"')).map(el => el.id)
        let selected_variants = productVariants.map(el => el.variant);
        let available_variants = all_variants.filter(entry1 => !selected_variants.some(entry2 => entry1 == entry2))
        setProductVariants([...productVariants, {
            variant: available_variants[0],
            tags: []
        }])
    };

    // handle input change on tag input
    const handleInputTagOnChange = (value, index) => {
        let product_variants = [...productVariants]
        product_variants[index].tags = value
        if(product_variants[index].tags.length === 0){
            product_variants.splice(index, 1);
        }
        setProductVariants(product_variants)

        checkVariant()
    }

    // remove product variant
    const removeProductVariant = (index) => {
        let product_variants = [...productVariants]
        product_variants.splice(index, 1)
        setProductVariants(product_variants)

        checkVariant()
    }

    // check the variant and render all the combination
    const checkVariant = () => {
        let tags = [];

        productVariants.filter((item) => {
            tags.push(item.tags)
        })

        setProductVariantPrices([])

        getCombn(tags).forEach(item => {
            setProductVariantPrices(productVariantPrice => [...productVariantPrice, {
                id: 0,
                title: item,
                price: 0,
                stock: 0
            }])
        })
    }

    // combination algorithm
    function getCombn(arr, pre) {
        pre = pre || '';
        if (!arr.length) {
            return pre;
        }
        let ans = arr[0].reduce(function (ans, value) {
            return ans.concat(getCombn(arr.slice(1), pre + value + '/'));
        }, []);
        return ans;
    }


    console.log('product: ', product);
    console.log('productVariants: ', productVariants);
    console.log('productVariantPrices: ', productVariantPrices);
    console.log('images: ', images);
    console.log('previewImages: ', previewImages);


    // Save product
    let saveProduct = async (event) => {
        event.preventDefault();
        console.log('save button clicked!');
        console.log('productVariants: ', productVariants);
        console.log('productVariantPrices: ', productVariantPrices);
        console.log('images: ', images);
        console.log('previewImages: ', previewImages);

        const csrftoken = Cookies.get('csrftoken');

        // TODO : write your code here to save the product
        if (product.title !== "" && product.sku !== "" && product.description !== "") {
            const filteredImages = []
            if(images.length > 0){
                images.forEach((imageObj)=>{
                    filteredImages.push(imageObj.image)
                })
            }
            let productData = {
                ...product,
                productVariantPrices: productVariantPrices,
                productVariants: productVariants,
                images: filteredImages
            }

            const formData = jsonToFormData(productData);

            const response = await fetch(CREATE_PRODUCT_URL, {
                method: 'POST',
                headers: {
                    // 'Content-Type': 'multipart/form-data',
                    'X-CSRFToken': csrftoken,
                },
                mode: 'same-origin',
                body: formData
            });
            console.log('save response: ', response);
            const data = await response.json();
            console.log('save response.data: ', data);
            if (response.status == 201) {
                alert(data.message);
                window.location.href = '/product/list/'
            }
            else {
                if (data.error) {
                    let errorMessage = ""
                    Object.entries(data.error).forEach((value, key) => {
                        errorMessage += `${value[0]}: ${value[1]}\n`
                    });
                    alert(errorMessage);
                }
            }
        } else {
            alert("title, sku and description are required");
        }
    }


    // Update product
    let updateProduct = async (event) => {
        event.preventDefault();
        console.log('update button clicked!');
        console.log('productVariants: ', productVariants);
        console.log('productVariantPrices: ', productVariantPrices);
        console.log('images: ', images);
        console.log('previewImages: ', previewImages);

        const csrftoken = Cookies.get('csrftoken');

        // TODO : write your code here to save the product
        if (product.title !== "" && product.sku !== "" && product.description !== "") {
            let updateImages = []
            if (images.length > 0){
                images.forEach((imageObj)=>{
                    if ((imageObj.id).toString().startsWith('lo')){
                        updateImages.push(imageObj.image);
                    }
                })
            }
            let productData = {
                ...product,
                productVariantPrices: productVariantPrices,
                productVariants: productVariants,
                images: updateImages
            }

            const formData = jsonToFormData(productData);

            const response = await fetch(`${PRODUCT_URL}${productId}`, {
                method: 'PUT',
                headers: {
                    // 'Content-Type': 'application/json'
                    // 'Content-Type': 'multipart/form-data; boundary=---WebKitFormBoundary7MA4YWxkTrZu0gW',
                    // 'Content-Type': 'multipart/form-data',
                    'X-CSRFToken': csrftoken,
                },
                mode: 'same-origin',
                body: formData
            });
            console.log('update response: ', response);
            const data = await response.json();
            console.log('update response.data: ', data);
            if (response.status == 200) {
                alert(data.message);
                setReRender(!reRender);
                // window.location.href = '/product/list/'
            }
            else {
                if (data.error) {
                    let errorMessage = ""
                    Object.entries(data.error).forEach((value, key) => {
                        errorMessage += `${value[0]}: ${value[1]}\n`
                    });
                    alert(errorMessage);
                }
            }
        } else {
            alert("title, sku and description are required");
        }
    }


    // Delete product image
    let deleteProductImage = async (productImageId) => {

        const csrftoken = Cookies.get('csrftoken');

        // TODO : write your code here to save the product
        if (productImageId && !productImageId.toString().startsWith('lo')) {

            const response = await fetch(`${PRODUCT_IMAGE_URL}${productImageId}`, {
                method: 'DELETE',
                headers: {
                    // 'Content-Type': 'application/json'
                    'X-CSRFToken': csrftoken,
                },
                mode: 'same-origin',
            });
            console.log('delete response: ', response);
            const data = await response.json();
            console.log('delete response.data: ', data);
            if (response.status == 200) {
                alert(data.message);
                setReRender(!reRender);
            }
            else {
                if (data.error) {
                    let errorMessage = ""
                    Object.entries(data.error).forEach((value, key) => {
                        errorMessage += `${value[0]}: ${value[1]}\n`
                    });
                    alert(errorMessage);
                }
            }
        } else {
            const filteredNewImages = images.filter((image)=> image.id !== productImageId);
            const filterePreviewImages = previewImages.filter((image)=> image.id !== productImageId);
            setImages([...filteredNewImages]);
            setPreviewImages([...filterePreviewImages]);
            
            alert(`Image with id ${productImageId} removed successfully!`);
        }
    }


    return (
        <div>
            <section>
                <div className="row">
                    <div className="col-md-6">
                        <div className="card shadow mb-4">
                            <div className="card-body">
                                <div className="form-group">
                                    <label htmlFor="">Product Name</label>
                                    <input onChange={(e) => handleProductFieldsChange(e)} defaultValue={product.title} name="title" type="text" placeholder="Product Name" className="form-control" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="">Product SKU</label>
                                    <input onChange={(e) => handleProductFieldsChange(e)} defaultValue={product.sku} name="sku" type="text" placeholder="Product SKU" className="form-control" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="">Description</label>
                                    <textarea onChange={(e) => handleProductFieldsChange(e)} defaultValue={product.description} name="description" cols="30" rows="4" className="form-control" />
                                </div>
                            </div>
                        </div>

                        <div className="card shadow mb-4">
                            <div
                                className="card-header py-3 d-flex flex-row align-items-center justify-content-between">
                                <h6 className="m-0 font-weight-bold text-primary">Media</h6>
                            </div>
                            <div className="card-body border">
                                <Dropzone onDrop={acceptedFiles => {
                                    console.log('acceptedFiles: ', acceptedFiles)
                                    if (acceptedFiles.length > 0) {
                                        let uploadableImages = []
                                        let newPreviewImages = []
                                        acceptedFiles.forEach((file, index) => {
                                            console.log('file: ', file);
                                            uploadableImages.push({ id: `local${index + 1}`, image: file });
                                            newPreviewImages.push({ id: `local${index + 1}`, image: URL.createObjectURL(file) });
                                        });
                                        setImages([...images, ...uploadableImages])
                                        setPreviewImages([...previewImages, ...newPreviewImages]);
                                    };
                                }}>
                                    {({ getRootProps, getInputProps }) => (
                                        <section>
                                            <div {...getRootProps()} className="h-25vh w-40vw card-body border d-flex justify-content-center align-items-center">
                                                <input {...getInputProps()} />
                                                <p>Drag 'n' drop some files here, or click to select files</p>
                                            </div>
                                        </section>
                                    )}
                                </Dropzone>
                            </div>
                        </div>
                        {
                            previewImages.length > 0 && (

                                <div className="card shadow mb-4">
                                    <div
                                        className="card-header py-3 d-flex flex-row align-items-center justify-content-between">
                                        <h6 className="m-0 font-weight-bold text-primary">Product Images</h6>
                                    </div>
                                    <div className="card-body border">
                                        <div className="d-flex flex-wrap justify-content-center align-items-center">
                                            {
                                                previewImages.map((imageItem, index) => (
                                                    <div key={index} className="border border-success m-2">
                                                        <div className="d-flex flex-column justify-content-center align-items-center">
                                                            <input style={{ color: 'red', width: '80px' }} type="button" value="Remove"
                                                                onClick={() => {
                                                                    deleteProductImage(imageItem.id);
                                                                }}
                                                            />
                                                            <img
                                                                src={imageItem.image}
                                                                className="m-1"
                                                                width={100}
                                                                height={100}
                                                                alt="Not found"
                                                            />
                                                        </div>
                                                    </div>
                                                ))
                                            }
                                        </div>
                                    </div>
                                </div>
                            )
                        }
                    </div>

                    <div className="col-md-6">
                        <div className="card shadow mb-4">
                            <div
                                className="card-header py-3 d-flex flex-row align-items-center justify-content-between">
                                <h6 className="m-0 font-weight-bold text-primary">Variants</h6>
                            </div>
                            <div className="card-body">
                                {
                                    productVariants.map((element, index) => {
                                        return (
                                            <div className="row" key={index}>
                                                <div className="col-md-4">
                                                    <div className="form-group">
                                                        <label htmlFor="">Option</label>
                                                        <select className="form-control" defaultValue={element.variant}>
                                                            {
                                                                JSON.parse(props.variants.replaceAll("'", '"')).map((variant, index) => {
                                                                    return (<option key={index}
                                                                        value={variant.id}>{variant.title}</option>)
                                                                })
                                                            }

                                                        </select>
                                                    </div>
                                                </div>

                                                <div className="col-md-8">
                                                    <div className="form-group">
                                                        {
                                                            productVariants.length > 1
                                                                ? <label htmlFor="" className="float-right text-primary"
                                                                    style={{ marginTop: "-30px" }}
                                                                    onClick={() => removeProductVariant(index)}>remove</label>
                                                                : ''
                                                        }

                                                        <section style={{ marginTop: "30px" }}>
                                                            <TagsInput value={element.tags}
                                                                style="margin-top:30px"
                                                                onChange={(value) => handleInputTagOnChange(value, index)} />
                                                        </section>

                                                    </div>
                                                </div>
                                            </div>
                                        )
                                    })
                                }


                            </div>
                            <div className="card-footer">
                                {productVariants.length !== 3
                                    ? <button className="btn btn-primary" onClick={handleAddClick}>Add another
                                        option</button>
                                    : ''
                                }

                            </div>

                            <div className="card-header text-uppercase">Preview</div>
                            <div className="card-body">
                                <div className="table-responsive">
                                    <table className="table">
                                        <thead>
                                            <tr>
                                                <td>Variant</td>
                                                <td>Price</td>
                                                <td>Stock</td>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {
                                                productVariantPrices.map((productVariantPrice, index) => {
                                                    return (
                                                        <tr key={index}>
                                                            <td>{productVariantPrice.title}</td>
                                                            <td>
                                                                <input
                                                                    className="form-control" 
                                                                    type="number"
                                                                    name="price"
                                                                    value={productVariantPrice.price}
                                                                    onChange={(e) => {
                                                                        handlePriceChange(e, index);
                                                                        console.log(`price${index}: ${e.target.value}`);
                                                                        // productVariantPrices[index].price = e.target.value;
                                                                    }}
                                                                    />
                                                            </td>
                                                            <td>
                                                                <input
                                                                    className="form-control"
                                                                    type="number"
                                                                    name="stock"
                                                                    value={productVariantPrice.stock}
                                                                    onChange={(e) => {
                                                                        handleStockChange(e, index);
                                                                        console.log(`stock${index}: ${e.target.value}`);
                                                                        // productVariantPrices[index].stock = e.target.value;
                                                                    }}
                                                                />
                                                            </td>
                                                        </tr>
                                                    )
                                                })
                                            }
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                {
                    productId == 'new' ? (
                        <button type="button" onClick={saveProduct} className="btn btn-lg btn-primary m-1">Save</button>
                    ) : (
                        <button type="button" onClick={updateProduct} className="btn btn-lg btn-primary m-1">Update</button>
                    )
                }

                <a href="/product/list/" className="btn btn-secondary btn-lg">Cancel</a>
            </section>
        </div>
    );
};

export default CreateProduct;
